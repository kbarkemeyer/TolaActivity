var assert = require('chai').assert;
var LoginPage = require('../pages/login.page.js');
var util = require('../lib/testutil.js');

describe('TolaActivity Login screen', function() {
  before(function() {
    this.timeout(0);
    browser.windowHandleMaximize();
  });

  it('should require unauthenticated user to authenticate', function() {
    let parms = util.readConfig();
    LoginPage.open(parms.baseurl);
    assert.equal('Mercy Corps Sign-On', browser.getTitle());
    LoginPage.setUserName(parms.username);
    LoginPage.setPassword(parms.password);
    LoginPage.clickLoginButton();
    // FIXME: Get the WebDriver code out of the test
    assert.equal('TolaActivity', browser.getTitle());
  });
});
