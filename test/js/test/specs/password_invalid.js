var assert = require('chai').assert;
var LoginPage = require('../pages/login.page.js');
var util = require('../lib/testutil.js');

describe('TolaActivity login screen', function() {
  before(function() {
    this.timeout(0);
    browser.windowHandleMaximize();
  });

  it('should deny access if password is invalid', function() {
    let parms = util.readConfig();
    // inject bogus password
    parms.password = 'ThisBetterFail';

    LoginPage.open(parms.baseurl);
    LoginPage.setUserName(parms.username);
    LoginPage.setPassword(parms.password);
    LoginPage.clickLoginButton();

    assert(browser.getText('#error').startsWith('Login failed:'));
  });
});
