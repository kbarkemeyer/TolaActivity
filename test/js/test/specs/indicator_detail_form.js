var assert = require('chai').assert;
var expect = require('chai').expect;
var LoginPage = require('../pages/login.page.js');
var IndPage = require('../pages/indicators.page.js');
var TargetsTab = require('../pages/targets.page.js');
var util = require('../lib/testutil.js');
const msec = 1000;

describe('Indicator creation detail form', function() {
  before(function() {
    // Disable timeouts
    this.timeout(0);
    browser.windowHandleMaximize();
    let parms = util.readConfig();
    LoginPage.open(parms.baseurl);
    LoginPage.setUserName(parms.username);
    LoginPage.setPassword(parms.password);
    LoginPage.clickLoginButton();
    IndPage.open();
    assert.equal('Program Indicators', IndPage.getPageName());
  });

  it('should exist', function() {
    IndPage.createBasicIndicator();
    browser.waitForVisible('h4');
    let title = browser.$('h4').getText().trim();
    expect(title.includes('Goal indicator: Temporary'),
      'Unexpected title text on the indicator detail screen');
  });

  describe('Summary tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Summary')); 
    });
  }); // end summary tab tests

  describe('Performance tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Performance')); 
    });
  }); // end performance tab tests

  describe('Targets tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Targets')); 
    });
  }); // end targets tab tests

  describe('Data Acquisition tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Data Acquisition')); 
    });
  }); // end data acquistion tab tests

  describe('Analysis and Reporting tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Analysis and Reporting')); 
    });
  }); // end analysis tab tests

  describe('Approval tab', function() {
    it('should exist', function() {
      expect(browser.isVisible('=Approval')); 
    });
  }); // end approval tab tests

  it('should have a Help link', function() {
    expect(browser.isVisible('=Help'));
  });

  it('should have a Save Changes button', function() {
    expect(browser.isVisible('=Save changes'));
  });

  it('should have a Reset button', function() {
    expect(browser.isVisible('=Reset'));
  });

  it('should restore form to pre-edit state when Reset button is clicked', function() {
    let select = browser.$('select#id_sector');
    let options = select.$$('option');
    let option = options[1];
    let origVal = option.getValue();

    // 2 - Basic Needs
    select.selectByValue(2);
    let newVal =  select.getValue();
    assert.equal(2, newVal, 'Unexpected selection mismatch');
    IndPage.clickResetButton();
    let resetVal = options[1].getValue();
    assert.equal(origVal, resetVal, 'Unexpected selection mismatch after Reset');
  });
}); // end create indicator detail page tests
