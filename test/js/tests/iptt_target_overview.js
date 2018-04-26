import IpttPage from '../pages/iptt.page';
import LoginPage from '../pages/login.page';
import Util from '../lib/testutil';
import { expect } from 'chai';
'use strict';

/**
 * IPTT report: Program target overview quickstart
 * Tests from mc/issues/119
 */
describe('IPTT report: Program target overview quickstart', function() {
    before(function() {
        // Disable timeouts
        this.timeout(0);
        browser.windowHandleMaximize();
        let parms = Util.readConfig();

        LoginPage.open(parms.baseurl);
        if (parms.baseurl.includes('mercycorps.org')) {
            LoginPage.username = parms.username;
            LoginPage.password = parms.password;
            LoginPage.login.click();
        } else if (parms.baseurl.includes('localhost')) {
            LoginPage.googleplus.click();
            if (LoginPage.title != 'TolaActivity') {
                LoginPage.gUsername = parms.username + '@mercycorps.org';
                LoginPage.gPassword = parms.password;
            }
        }        
    });
   
    it('should exist', function () {
        IpttPage.open();
        expect('Indicator Performance Tracking Table' == 
            IpttPage.title);
        expect('Program target overview' ==
            IpttPage.quickstart('target'));
    });

    it('should have Program dropdown', function() {
        IpttPage.TargetOverviewProgram.click();
    });

    it('should have a Target periods dropdown', function() {
        IpttPage.TargetOverviewTargetPeriods.click();
    });

    it('should allow to select time frame', function() {
        let val = IpttPage.TargetOverviewTimeFrame;
        expect(val != undefined);
        expect(val != null);
    });

    it('should require choosing a program', function() {
        // Select a target period but not a program
        IpttPage.TargetOverviewTimePeriods = 'Annual';
        expect(IpttPage.TargetOverviewViewReport.disable == 'disabled');
    });

    it('should require choosing a target period', function() {
        // Select a program but not a target period
        //FIXME: magic number
        IpttPage.TargetOverviewProgram = 2;
        expect(IpttPage.TargetOverviewViewReport.disable == 'disabled');
    });

    it('should only show indicator combos with compatible target periods');
    it('should not show indicator combos with incompatible target periods');
    it('should show indicators with compatible and incompatible target periods in separate tables');

    it('should open report with filter panel open', function() {
        expect(true == browser.isVisible('form#id_form_target_Filter'));
    });
}); 
