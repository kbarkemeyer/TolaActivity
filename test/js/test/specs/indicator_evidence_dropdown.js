var assert = require('chai').assert;
var LoginPage = require('../pages/login.page.js');
var IndPage = require('../pages/indicators.page.js');
var TargetsTab = require('../pages/targets.page.js');
var util = require('../lib/testutil.js');
const msec = 1000;

describe('Program Indicators page', function() {
  before(function() {
    // Disable timeouts
    this.timeout(0);
    browser.windowHandleMaximize();
    let parms = util.readConfig();
    LoginPage.open(parms.baseurl);
    LoginPage.setUserName(parms.username);
    LoginPage.setPassword(parms.password);
    LoginPage.clickLoginButton();
  });

  describe('Indicator evidence dropdown', function() {
    it('should be able to view PI evidence table by clicking its Data button');
    it('should decrease evidence count when PI evidence deleted');
    it('should increase evidence count when PI evidence added');
    it("should toggle indicator's evidence dropdown by clicking its Data button");
    it('should have the same row count as evidence count on Data button');
    it('should be able to edit evidence line item by clicking its Edit button');
    it('should be able to edit evidence line item by clicking its Indicator Name');
    it('should open Collected Data form when editing evidence line item');
    it('should be able to delete evidence line item by clicking its Delete button');
    it('should be able to add evidence line item by clicking the New Data button');
    it('should open blank Collected Data form when the New Data button is clicked');
  });
});
