import bisect
from collections import OrderedDict
from dateutil import rrule, parser
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.core.urlresolvers import reverse_lazy
from django.db.models import Sum, Avg, Subquery, OuterRef, Case, When, Q, F, Max
from django.views.generic import TemplateView, FormView
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.contrib import messages
from tola.util import formatFloat
from workflow.models import Program
from ..models import Indicator, CollectedData, Level, PeriodicTarget
from ..forms import IPTTReportQuickstartForm, IPTTReportFilterForm
from ..templatetags.mytags import symbolize_change, symbolize_measuretype


class IPTTReportQuickstartView(FormView):
    template_name = 'indicators/iptt_quickstart.html'
    form_class = IPTTReportQuickstartForm
    FORM_PREFIX_TIME = 'timeperiods'
    FORM_PREFIX_TARGET = 'targetperiods'

    def get_context_data(self, **kwargs):
        context = super(IPTTReportQuickstartView, self).get_context_data(**kwargs)

        # Add two instances of the same form to context if they're not present
        if 'form' not in context:
            context['form'] = self.form_class(request=self.request, prefix=self.FORM_PREFIX_TIME)
        if 'form2' not in context:
            context['form2'] = self.form_class(request=self.request, prefix=self.FORM_PREFIX_TARGET)
        return context

    def get_form_kwargs(self):
        kwargs = super(IPTTReportQuickstartView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        targetprefix = request.POST.get('%s-formprefix' % self.FORM_PREFIX_TARGET)
        timeprefix = request.POST.get('%s-formprefix' % self.FORM_PREFIX_TIME)

        # set prefix to the current form
        if targetprefix is not None:
            prefix = targetprefix
        else:
            prefix = timeprefix

        form = IPTTReportQuickstartForm(self.request.POST, prefix=prefix, request=self.request)

        # call the form_valid/invalid with the correct prefix and form
        if form.is_valid():
            return self.form_valid(**{'form': form, 'prefix': prefix})
        else:
            return self.form_invalid(**{'form': form, 'prefix': prefix})

    def form_valid(self, **kwargs):
        context = self.get_context_data()
        form = kwargs.get('form')
        prefix = kwargs.get('prefix')

        if prefix == self.FORM_PREFIX_TARGET:
            period = form.cleaned_data.get('targetperiods')
            context['form2'] = form
            context['form'] = self.form_class(request=self.request,
                                              prefix=self.FORM_PREFIX_TIME)
        else:
            prefix = self.FORM_PREFIX_TIME
            period = form.cleaned_data.get('timeperiods')
            context['form'] = form
            context['form2'] = self.form_class(request=self.request,
                                               prefix=self.FORM_PREFIX_TARGET)

        program = form.cleaned_data.get('program')
        num_recents = form.cleaned_data.get('numrecentperiods')
        timeframe = form.cleaned_data.get('timeframe')
        redirect_url = reverse_lazy('iptt_report', kwargs={'program_id': program.id, 'reporttype': prefix})

        redirect_url = "{}?{}={}&timeframe={}".format(redirect_url, prefix, period, timeframe)
        if num_recents:
            redirect_url = "{}&numrecentperiods={}".format(redirect_url, num_recents)
        return HttpResponseRedirect(redirect_url)

    def form_invalid(self, form, **kwargs):
        context = self.get_context_data()
        form = kwargs.get('form')
        if kwargs.get('prefix') == self.FORM_PREFIX_TARGET:
            context['form2'] = form
            context['form'] = self.form_class(request=self.request, prefix=self.FORM_PREFIX_TIME)
        else:
            context['form'] = form
            context['form2'] = self.form_class(request=self.request, prefix=self.FORM_PREFIX_TARGET)
        return self.render_to_response(context)


class IPTT_ReportView(TemplateView):
    template_name = 'indicators/iptt_report.html'
    REPORT_TYPE_TIMEPERIODS = 'timeperiods'
    REPORT_TYPE_TARGETPERIODS = 'targetperiods'

    MONTHS_PER_MONTH = 1
    MONTHS_PER_QUARTER = 3
    MONTHS_PER_TRIANNUAL = 4
    MONTHS_PER_SEMIANNUAL = 6
    MONTHS_PER_YEAR = 12

    def __init__(self, **kwars):
        self.program = None
        self.annotations = {}
        self.filter_form_initial_data = {}

    @staticmethod
    def _get_num_months(period):
        """
        Returns the number of months for a given time-period
        """
        try:
            return {
                Indicator.ANNUAL: IPTT_ReportView.MONTHS_PER_YEAR,
                Indicator.SEMI_ANNUAL: IPTT_ReportView.MONTHS_PER_SEMIANNUAL,
                Indicator.TRI_ANNUAL: IPTT_ReportView.MONTHS_PER_TRIANNUAL,
                Indicator.QUARTERLY: IPTT_ReportView.MONTHS_PER_QUARTER,
                Indicator.MONTHLY: IPTT_ReportView.MONTHS_PER_MONTH
                }[period]
        except KeyError:
            return 0

    @staticmethod
    def _get_period_name(period):
        """
        Returns the name of the period
        """
        try:
            return {
                Indicator.ANNUAL: _('Year'),
                Indicator.SEMI_ANNUAL: _('Semi-annual'),
                Indicator.TRI_ANNUAL: _('Tri-annual'),
                Indicator.QUARTERLY: _('Quarter'),
                Indicator.MONTHLY: _('Month')
            }[period]
        except KeyError:
            return 0

    def _get_first_period(self, start_date, num_months_in_period):
        # TODO: Delete it
        if start_date is None:
            num_months_in_period = 0

        if num_months_in_period == IPTT_ReportView.MONTHS_PER_MONTH:
            # if interval is monthly, set the start_date to the first of the month
            period_start_date = start_date.replace(day=1)
        elif num_months_in_period == IPTT_ReportView.MONTHS_PER_QUARTER:
            # if interval is quarterly, set period_start_date to first calendar quarter
            quarter_start = [start_date.replace(month=month, day=1) for month in (1, 4, 7, 10)]
            index = bisect.bisect(quarter_start, start_date)
            period_start_date = quarter_start[index-1]
        elif num_months_in_period == IPTT_ReportView.MONTHS_PER_TRIANNUAL:
            # if interval is tri-annual, set period_start_date to first calendar tri-annual
            tri_annual_start = [start_date.replace(month=month, day=1) for month in (1, 5, 9)]
            index = bisect.bisect(tri_annual_start, start_date)
            period_start_date = tri_annual_start[index-1]
        elif num_months_in_period == IPTT_ReportView.MONTHS_PER_SEMIANNUAL:
            # if interval is semi-annual, set period_start_date to first calendar semi-annual
            semi_annual = [start_date.replace(month=month, day=1) for month in (1, 7)]
            index = bisect.bisect(semi_annual, start_date)
            period_start_date = semi_annual[index-1]
        elif num_months_in_period == IPTT_ReportView.MONTHS_PER_YEAR:
            # if interval is annual, set period_start_date to first calendar year
            period_start_date = start_date.replace(month=1, day=1)
        else:
            period_start_date = None

        return period_start_date

    def _generate_annotations(self, timeperiods, period, reporttype):
        """
        Generates queryset annotation(sum, avg, last data record). All three annotations are calculated
        because one of these three values will be used depending on how an indicator is configured.
        """
        if period == Indicator.LOP:
            self.annotations = {}
        elif period == Indicator.MID_END:
            # Create annotations for MIDLINE TargetPeriod
            last_data_record = CollectedData.objects.filter(
                indicator=OuterRef('pk'),
                periodic_target__period=PeriodicTarget.MIDLINE)\
                .order_by('-id')
            midline_sum = Sum(
                Case(
                    When(
                        Q(unit_of_measure_type=Indicator.NUMBER) &
                        Q(collecteddata__periodic_target__period=PeriodicTarget.MIDLINE),
                        then=F('collecteddata__achieved')
                    )
                )
            )
            # midline_avg = Avg(
            #     Case(
            #         When(
            #             Q(unit_of_measure_type=Indicator.PERCENTAGE) &
            #             Q(is_cumulative=False) &
            #             Q(collecteddata__periodic_target__period=PeriodicTarget.MIDLINE),
            #             then=F('collecteddata__achieved')
            #         )
            #     )
            # )
            midline_last = Max(
                Case(
                    When(
                        Q(unit_of_measure_type=Indicator.PERCENTAGE) &
                        # Q(is_cumulative=True) &
                        Q(collecteddata__periodic_target__period=PeriodicTarget.MIDLINE),
                        then=Subquery(last_data_record.values('achieved')[:1])
                    )
                )
            )
            # Get the midline target value
            midline_target = Max(
                Case(
                    When(
                        Q(collecteddata__periodic_target__period=PeriodicTarget.MIDLINE),
                        then=Subquery(last_data_record.values('periodic_target__target')[:1])
                    )
                )
            )

            # Create annotations for ENDLINE TargetPeriod
            last_data_record = CollectedData.objects.filter(
                indicator=OuterRef('pk'),
                periodic_target__period=PeriodicTarget.ENDLINE)\
                .order_by('-id')
            endline_sum = Sum(
                Case(
                    When(
                        Q(unit_of_measure_type=Indicator.NUMBER) &
                        Q(collecteddata__periodic_target__period=PeriodicTarget.ENDLINE),
                        then=F('collecteddata__achieved')
                    )
                )
            )
            # endline_avg = Avg(
            #     Case(
            #         When(
            #             Q(unit_of_measure_type=Indicator.PERCENTAGE) &
            #             Q(is_cumulative=False) &
            #             Q(collecteddata__periodic_target__period=PeriodicTarget.ENDLINE),
            #             then=F('collecteddata__achieved')
            #         )
            #     )
            # )
            endline_last = Max(
                Case(
                    When(
                        Q(unit_of_measure_type=Indicator.PERCENTAGE) &
                        # Q(is_cumulative=True) &
                        Q(collecteddata__periodic_target__period=PeriodicTarget.ENDLINE),
                        then=Subquery(last_data_record.values('achieved')[:1])
                    )
                )
            )
            # Get the endline target value
            endline_target = Max(
                Case(
                    When(
                        Q(collecteddata__periodic_target__period=PeriodicTarget.ENDLINE),
                        then=Subquery(last_data_record.values('periodic_target__target')[:1])
                    )
                )
            )
            self.annotations["Midline_target"] = midline_target
            self.annotations["Endline_target"] = endline_target
            self.annotations['Midline_sum'] = midline_sum
            # self.annotations['Midline_avg'] = midline_avg
            self.annotations['Midline_last'] = midline_last
            self.annotations['Endline_sum'] = endline_sum
            # self.annotations['Endline_avg'] = endline_avg
            self.annotations['Endline_last'] = endline_last
        else:
            for k, v in timeperiods.items():
                start_date = datetime.strftime(v[0], '%Y-%m-%d')
                end_date = datetime.strftime(v[1], '%Y-%m-%d')

                last_data_record = CollectedData.objects.filter(
                    indicator=OuterRef('pk'),
                    date_collected__gte=start_date,
                    date_collected__lte=end_date)\
                    .order_by('-pk')

                annotation_sum = Sum(
                    Case(
                        When(
                            Q(unit_of_measure_type=Indicator.NUMBER) &
                            Q(collecteddata__date_collected__gte=start_date) &
                            Q(collecteddata__date_collected__lte=end_date),
                            then=F('collecteddata__achieved')
                        )
                    )
                )

                # annotation_avg = Avg(
                #     Case(
                #         When(
                #             Q(unit_of_measure_type=Indicator.PERCENTAGE) &
                #             Q(is_cumulative=False) &
                #             Q(collecteddata__date_collected__gte=start_date) &
                #             Q(collecteddata__date_collected__lte=end_date),
                #             then=F('collecteddata__achieved')
                #         )
                #     )
                # )
                annotation_last = Max(
                    Case(
                        When(
                            Q(unit_of_measure_type=Indicator.PERCENTAGE) &
                            # Q(is_cumulative=True) &
                            Q(collecteddata__date_collected__gte=start_date) &
                            Q(collecteddata__date_collected__lte=end_date),
                            then=Subquery(last_data_record.values('achieved')[:1])
                        )
                    )
                )

                # if this is targetperiods IPTT report then get the target value for each period
                if reporttype == self.REPORT_TYPE_TARGETPERIODS:
                    annotation_target = Max(
                        Case(
                            When(
                                Q(collecteddata__date_collected__gte=start_date) &
                                Q(collecteddata__date_collected__lte=end_date),
                                then=Subquery(last_data_record.values('periodic_target__target')[:1])
                            )
                        )
                    )
                    self.annotations["{}_target".format(k)] = annotation_target

                # the following becomes annotations for the queryset
                # e.g.
                # Year 1_sum=..., Year 2_sum=..., etc.
                # Year 1_avg=..., Year 2_avg=..., etc.
                # Year 1_last=..., Year 2_last=..., etc.
                #
                self.annotations["{}_sum".format(k)] = annotation_sum
                # self.annotations["{}_avg".format(k)] = annotation_avg
                self.annotations["{}_last".format(k)] = annotation_last
        return self.annotations

    def _get_num_periods(self, start_date, end_date, period):
        """
        Returns the number of periods depending on the period is in terms of months
        """
        num_months_in_period = self._get_num_months(period)
        total_num_months = len(list(rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date)))
        try:
            num_periods = total_num_months / num_months_in_period
            remainder_months = total_num_months % num_months_in_period
            if remainder_months > 0:
                num_periods += 1
        except ZeroDivisionError:
            num_periods = 0
        return num_periods

    def _generate_targetperiods(self, program, period, num_recents):
        targetperiods = OrderedDict()
        today = datetime.today().date()
        # today = datetime.strptime('2020-02-23', '%Y-%m-%d').date()

        # All indicators within a program that have the same target_frequency (annual, monthly, etc)
        # have the same number of target periods with the same start and end dates, thus we can just
        # get the first indicator that is within this program and have the same target_frequency(period)
        # and fetch the related set of periodic_targets
        ind = Indicator.objects.filter(program__in=[program.id], target_frequency=period).first()
        periodic_targets = PeriodicTarget.objects.filter(indicator=ind)\
            .values("id", "period", "target", "start_date", "end_date")

        try:
            start_date = parser.parse(self.filter_form_initial_data['start_date']).date()
            end_date = parser.parse(self.filter_form_initial_data['end_date']).date()
            periodic_targets = periodic_targets.filter(start_date__gte=start_date, end_date__lte=end_date)
        except (KeyError, ValueError):
            pass

        for pt in periodic_targets:
            # if it is LOP Target then do not show any target periods becaseu there are none.
            if pt['period'] == Indicator.TARGET_FREQUENCIES[0][1]:
                continue
            targetperiods[pt['period']] = [pt['start_date'], pt['end_date'], pt['target'], pt['id']]

        if num_recents is not None and num_recents > 0 and period not in [Indicator.LOP, Indicator.MID_END]:
            # filter out those timeperiods whose end_dates are larger than today's date
            targetperiods_less_than_today = filter(lambda v: v[1][0] <= today, targetperiods.items())

            # filter out dates that are outside of the most_recent index specified by user
            most_recent_targetperiods = targetperiods_less_than_today[(
                len(targetperiods_less_than_today)-num_recents):]

            # convert to oredered dictionary to preserve order (IMPORTANT!)
            targetperiods = OrderedDict((k, v) for k, v in most_recent_targetperiods)
        return targetperiods

    def _generate_timeperiods(self, filter_start_date, filter_end_date, frequency, show_all, num_recents):
        timeperiods = OrderedDict()
        today_date = datetime.today().date()
        # today_date = datetime.strptime('2020-02-23', '%Y-%m-%d').date()

        period_name = self._get_period_name(frequency)
        num_months_in_period = self._get_num_months(frequency)

        # Get the first day of the period that encomposses today's date
        current_period_start = today_date.replace(month=self.program.reporting_period_start.month, day=1)

        # Now calculate the last day of the current period that encompasses today's date
        current_period_end = current_period_start + relativedelta(months=+num_months_in_period)

        num_periods = self._get_num_periods(self.program.reporting_period_start,
                                            self.program.reporting_period_end, frequency)

        start_date = self.program.reporting_period_start

        # bump up num_periods by 1 because the loop starts from 1 instead of 0
        num_periods += 1
        for i in range(1, num_periods):
            if i > 1:
                # if it is not the first period then advance the
                # start_date by the correct number of months.
                start_date = start_date + relativedelta(months=+num_months_in_period)

            end_date = start_date + relativedelta(months=+num_months_in_period) + relativedelta(days=-1)
            # print('start_date={}, end_date={}'.format(start_date, end_date))
            timeperiods["{} {}".format(period_name, i)] = [start_date, end_date]

        # Update the report_end_date with the last reporting_period's end_date
        try:
            report_end_date = timeperiods[timeperiods.keys()[-1]][1]
        except TypeError:
            report_end_date = self.program.reporting_period_end

        if num_recents is not None and num_recents > 0:
            # filter out those timeperiods whose end_dates are larger than today's date
            timeperiods_less_than_today = filter(lambda v: v[1][1] < current_period_end, timeperiods.items())

            # filter out dates that are outside of the most_recent index specified by user
            most_recent_timeperiods = timeperiods_less_than_today[(len(timeperiods_less_than_today)-num_recents):]

            # convert to oredered dictionary to preserve order (IMPORTANT!)
            timeperiods = OrderedDict((k, v) for k, v in most_recent_timeperiods)
        elif show_all == 0 and filter_start_date is not None and filter_end_date is not None:
            filtered_timeperiods = OrderedDict()
            for k, v in timeperiods.items():
                start_date = v[0]
                end_date = v[1]
                # print("start_date:{}, filter_start_date:{}, filter_end_date:{}, end_date:{}".format(start_date, filter_start_date, filter_end_date, end_date))
                if start_date >= filter_start_date and filter_end_date >= end_date:
                    filtered_timeperiods[k] = [start_date, end_date]
            return (report_end_date, filtered_timeperiods)

        return (report_end_date, timeperiods)

    def _update_filter_form_initial(self, formdata):
        self.filter_form_initial_data = {}
        for k in formdata:
            v = formdata.getlist(k)
            if k == 'csrfmiddlewaretoken' or k == 'program':
                continue
            if isinstance(v, list) and len(v) == 1:
                v = v[0]

            if k == self.REPORT_TYPE_TIMEPERIODS or k == self.REPORT_TYPE_TARGETPERIODS:
                try:
                    v = int(v)
                except ValueError:
                    v = int(Indicator.ANNUAL)  # defaults to annual

            if k == 'numrecentperiods':
                try:
                    v = int(v)
                except ValueError:
                    continue
            # print("{} = {}".format(k, v))
            self.filter_form_initial_data[k] = v

    def _get_filters(self, data):
        filters = {}
        try:
            filters['level__in'] = data['level']
        except KeyError:
            pass
        try:
            filters['sector__in'] = data['sector']
        except KeyError:
            pass
        try:
            filters['indicator_type__in'] = data['ind_type']
        except KeyError:
            pass
        try:
            filters['collecteddata__site__in'] = data['site']
        except KeyError:
            pass
        try:
            filters['id__in'] = data['indicators'] if isinstance(data['indicators'], list) else [data['indicators']]
        except KeyError:
            pass
        return filters

    def prepare_indicators(self, reporttype, period, periods_date_ranges, indicators):
        # Calculate the cumulative sum across timeperiods for indicators that are NUMBER and CUMULATIVE
        for i, ind in enumerate(indicators):
            running_total = 0
            # process indicator number
            if ind['number'] is None:
                ind['number'] = ''

            # process level
            if ind['lastlevel'] is None:
                ind['lastlevel'] = ''

            # process unit_of_measure
            if ind['unit_of_measure'] is None:
                ind['unit_of_measure'] = ''

            # process direction_of_change
            ind['direction_of_change'] = symbolize_change(ind['direction_of_change'])

            # process indicator is_cumulative status
            if ind['target_frequency'] == Indicator.LOP:
                ind['cumulative'] = _("N/A")
            elif ind['is_cumulative'] is True:
                ind['cumulative'] = _("Cumulative")
            elif ind['is_cumulative'] is False:
                ind['cumulative'] = _("Non-cumulative")

            # process indicator_unit_type
            ind['unittype'] = symbolize_measuretype(ind['unit_of_measure_type'])

            # process baseline
            if ind['baseline_na'] is True:
                ind['baseline'] = _("N/A")
            else:
                if ind['baseline'] is None:
                    ind['baseline'] = ''

            # process lop_target
            try:
                lop_target = float(ind['lop_target'])
                if ind['unit_of_measure_type'] == Indicator.PERCENTAGE:
                    ind['lop_target'] = "{}%".format(formatFloat(lop_target))
                else:
                    ind['lop_target'] = formatFloat(lop_target)
            except (ValueError, TypeError):
                lop_target = ''
                ind['lop_target'] = lop_target

            # process lop_actual
            lop_actual = ''
            percent = ''
            if ind['unit_of_measure_type'] == Indicator.NUMBER:
                if ind['actualsum'] is not None:
                    lop_actual = float(ind['actualsum'])
            elif ind['unit_of_measure_type'] == Indicator.PERCENTAGE:
                if ind['lastdata'] is not None:
                    lop_actual = float(ind['lastdata'])
                    percent = "%"
            try:
                ind['lop_actual'] = "{}{}".format(formatFloat(lop_actual), percent)
            except TypeError:
                ind['lop_actual'] = ''

            # process lop_percent_met
            try:
                ind['lop_percent_met'] = "{}%".format(formatFloat(lop_actual / lop_target * 100))
            except TypeError:
                # print('actual={}, lop={}'.format(lop_actual, lop_target))
                ind['lop_percent_met'] = ''

            if period in [Indicator.ANNUAL, Indicator.SEMI_ANNUAL, Indicator.TRI_ANNUAL, Indicator.QUARTERLY,
                          Indicator.MONTHLY, Indicator.MID_END]:
                # if the frequency (period) is periodic, i.e., time-aware then go through each period
                # and calculate the cumulative total achieved across date ranges (periods)
                for k, v in periods_date_ranges.items():
                    if ind['unit_of_measure_type'] == Indicator.NUMBER and ind['is_cumulative'] is True:
                        current_sum = ind["{}_sum".format(k)]
                        if current_sum is not None:
                            # current_sum = 0
                            key = "{}_rsum".format(k)
                            running_total = running_total + current_sum
                            ind[key] = running_total

                    # process target_period actual value
                    actual = '{}_actual'.format(k)
                    actual_val = ''
                    percent_sign = ''
                    if ind['unit_of_measure_type'] == Indicator.NUMBER:
                        if ind['is_cumulative'] is True:
                            try:
                                actual_val = ind["{}_rsum".format(k)]
                            except KeyError:
                                actual_val = ''
                        else:  # if it is not set to cumulative then default to non-cumulative even it is it not set
                            actual_val = ind["{}_sum".format(k)]
                    elif ind['unit_of_measure_type'] == Indicator.PERCENTAGE:
                        percent_sign = '%'
                        actual_val = ind["{}_last".format(k)]

                    if actual_val is not None and actual_val != '':
                        ind[actual] = "{}{}".format(formatFloat(actual_val), percent_sign)
                    else:
                        ind[actual] = ''

                    if reporttype == self.REPORT_TYPE_TARGETPERIODS:
                        # process target_period target value
                        target_key = "{}_target".format(k)
                        if ind[target_key] is None:
                            target_val = ''
                        else:
                            target_val = formatFloat(float(ind[target_key]))

                        if ind['unit_of_measure_type'] == Indicator.PERCENTAGE:
                            if target_val > 0 and target_val != '':
                                ind['{}_period_target'.format(k)] = "{}%".format(target_val)
                            else:
                                ind['{}_period_target'.format(k)] = ''
                        else:
                            ind['{}_period_target'.format(k)] = target_val

                        # process target_period percent_met value
                        try:
                            percent_met = '{}_percent_met'.format(k)
                            target = float(ind["{}_target".format(k)])
                            if ind['unit_of_measure_type'] == Indicator.NUMBER:
                                if ind['is_cumulative'] is True:
                                    rsum = float(ind["{}_rsum".format(k)])
                                    ind[percent_met] = formatFloat(rsum / target * 100)
                                else:
                                    ind[percent_met] = formatFloat(float(ind["{}_sum".format(k)]) / target * 100)
                            elif ind['unit_of_measure_type'] == Indicator.PERCENTAGE:
                                percent_met_val = formatFloat(float(ind["{}_last".format(k)]) / target * 100)
                                ind[percent_met] = "{}%".format(percent_met_val)
                        except TypeError:
                            ind[percent_met] = ''
        return indicators

    def get_context_data(self, **kwargs):
        context = super(IPTT_ReportView, self).get_context_data(**kwargs)
        reporttype = kwargs.get('reporttype')
        program_id = kwargs.get('program_id')

        try:
            self.program = Program.objects.get(pk=program_id)
        except Program.DoesNotExist:
            context['redirect'] = reverse_lazy('iptt_quickstart')
            messages.info(self.request, _("Please select a valid program."))
            return context

        self._update_filter_form_initial(self.request.GET)
        filters = self._get_filters(self.filter_form_initial_data)

        if reporttype == self.REPORT_TYPE_TIMEPERIODS:
            period = self.filter_form_initial_data[self.REPORT_TYPE_TIMEPERIODS]
        else:
            period = self.filter_form_initial_data[self.REPORT_TYPE_TARGETPERIODS]

        try:
            num_recents = self.filter_form_initial_data['numrecentperiods']
        except KeyError:
            num_recents = 0

        try:
            show_all = self.filter_form_initial_data['timeframe']
        except KeyError:
            show_all = 0

        # calculate aggregated actuals (sum, avg, last) per reporting period
        # (monthly, quarterly, tri-annually, seminu-annualy, and yearly) for each indicator
        lastlevel = Level.objects.filter(indicator__id=OuterRef('pk')).order_by('-id')
        last_data_record = CollectedData.objects.filter(indicator=OuterRef('pk')).order_by('-date_collected')
        indicators = Indicator.objects.filter(program__in=[program_id], **filters) \
            .annotate(actualsum=Sum('collecteddata__achieved'),
                      actualavg=Avg('collecteddata__achieved'),
                      lastlevel=Subquery(lastlevel.values('name')[:1]),
                      lastlevelcustomsort=Subquery(lastlevel.values('customsort')[:1]),
                      lastdata=Subquery(last_data_record.values('achieved')[:1]))\
            .values(
                'id', 'number', 'name', 'program', 'target_frequency', 'lastlevel', 'unit_of_measure',
                'direction_of_change', 'unit_of_measure_type', 'is_cumulative', 'baseline', 'baseline_na',
                'lop_target', 'actualsum', 'actualavg', 'lastdata', 'lastlevelcustomsort')

        report_start_date = self.program.reporting_period_start
        report_end_date = self.program.reporting_period_end

        try:
            start_date = datetime.strptime(
                self.filter_form_initial_data.get('start_date'), "%b %d, %Y").date()
            start_date = start_date.replace(month=report_start_date.month, day=1)
        except TypeError:
            # there is no start date specified so use the program start date
            start_date = report_start_date

        try:
            end_date = datetime.strptime(
                self.filter_form_initial_data.get('end_date'), "%b %d, %Y").date()
            end_date = end_date.replace(month=report_end_date.month)
        except TypeError:
            # end_date is not specified in the filter form
            end_date = report_end_date

        if reporttype == self.REPORT_TYPE_TIMEPERIODS:
            # Update the report_end_date to make sure it ends with the last period's end_date
            # Also, get the all of the periodic date ranges based on the selected period
            report_end_date, periods_date_ranges = self._generate_timeperiods(
                start_date, end_date, period, show_all, num_recents)
            # Get the last period's end_date
            last_filtered_period_date = periods_date_ranges[periods_date_ranges.keys()[-1]][1]
            # update the end_date with the last period's end_date to show in the tile and filter from
            end_date = end_date.replace(month=last_filtered_period_date.month, day=last_filtered_period_date.day)
            self.filter_form_initial_data['end_date'] = end_date
        elif reporttype == self.REPORT_TYPE_TARGETPERIODS:
            periods_date_ranges = self._generate_targetperiods(self.program, period, num_recents)
            indicators = indicators.filter(target_frequency=period)
        else:
            context['redirect'] = reverse_lazy('iptt_quickstart')
            messages.info(self.request, _("Please select a valid report type."))
            return context

        self.annotations = self._generate_annotations(periods_date_ranges, period, reporttype)
        # update the queryset with annotations for timeperiods
        indicators = indicators.annotate(**self.annotations).order_by('lastlevelcustomsort', 'number', 'name')
        indicators = self.prepare_indicators(reporttype, period, periods_date_ranges, indicators)

        context['start_date'] = start_date.strftime("%b %d, %Y")
        context['end_date'] = end_date.strftime("%b %d, %Y")  # self.filter_form_initial_data.get('end_date', report_end_date.strftime('%b %d, %Y'))
        context['report_start_date'] = report_start_date
        context['report_end_date'] = report_end_date
        context['report_date_ranges'] = periods_date_ranges
        context['indicators'] = indicators
        context['program'] = self.program
        context['reporttype'] = reporttype
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # if user has not specified a start_date/enddates already then set it so the filter form
        # shows the program reporting start_date
        if 'start_date' not in self.filter_form_initial_data \
                or self.filter_form_initial_data['start_date'] in ['None', None, '']:
            self.filter_form_initial_data['start_date'] = context['report_start_date']

        if 'end_date' not in self.filter_form_initial_data \
                or self.filter_form_initial_data['end_date'] in ['None', None, '']:
            self.filter_form_initial_data['end_date'] = context['report_end_date']

        form_kwargs = {'request': request, 'program': context['program']}
        context['form'] = IPTTReportFilterForm(initial=self.filter_form_initial_data, **form_kwargs)

        context['report_wide'] = True
        if context.get('redirect', None):
            return HttpResponseRedirect(reverse_lazy('iptt_quickstart'))
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        filterdata = request.POST.copy()
        print filterdata
        # no need to include this token in querystring
        del(filterdata['csrfmiddlewaretoken'])
        url_kwargs = {
            'program_id': filterdata['program'],
            'reporttype': kwargs['reporttype'],
        }
        # do not include it in the querystring because it is already part of the url kwargs
        del filterdata['program']
        redirect_url = "{}?{}".format(reverse_lazy('iptt_report', kwargs=url_kwargs),
                                      filterdata.urlencode())
        return HttpResponseRedirect(redirect_url)
