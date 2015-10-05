(function () {

  var app = angular.module('historia', ['ngCookies']);

  app.controller('historiaController', function() {
    this.tab = 1;

    this.isSet = function(checkTab) {
      return this.tab === checkTab;
    };

    this.setTab = function(activeTab) {
      this.tab = activeTab;
    };

  });

  app.controller('SubmissionController', ['$http', '$cookies',function($http, $cookies){

    this.parameters = [];
    this.targetUrl = "/historia";
    this.method = "";
    this.lastResponse = {};
    this.lastHeaders = "N/A";
    this.lastURL = "N/A";
    this.cookies = [];

    var submission = this;

    this.send_request = function() {
      // send the current values and see what's up.
      if (this.method){
        var request_url = [this.targetUrl, "?"]
        for (var i=0; i<this.parameters.length;i++) {
          request_url.push(this.parameters[i].name);
          request_url.push("=");
          request_url.push(this.parameters[i].value);
          request_url.push("&");
        }
        request_url.pop();
        $http.get(request_url.join("")).success(this.display_response).error(this.display_response);
      } else {

        var data = {};
        for (var i=0; i<this.parameters.length;i++) {
          data[this.parameters[i].name] = this.parameters[i].value;
        }

        $http.post(this.targetUrl, data).success(this.display_response).error(this.display_response);
      }
    }

    this.reset_params = function() {
      this.parameters = [];
    }

    this.display_response = function(data, status, headers, config) {
      submission.lastResponse = data;
      submission.lastHeaders = headers();
      submission.lastHeaders.status = status;
      submission.lastHeaders.url = config.url;
      submission.cookies = [];
      var allCookies = $cookies.getAll();
      for (var key in allCookies){
        if (allCookies.hasOwnProperty(key)){
          c = {"name": key, "value": allCookies[key]};
          submission.cookies.push(c);
        }
      }
    }

  }]);

  app.controller('ParameterController', function(){

    this.parameter = {}

    this.addParameter = function(submission) {
      submission.parameters.push(this.parameter);
      this.parameter = {};
    };

  });


  app.controller('UserLoginController', ['$http', '$cookies',function($http,$cookies){

    this.targetUrl = "/historia/system/user/login";
    this.username = $cookies.get('username');
    this.isLoggedIn = false;
    this.useradmin = "?";
    this.lastHeaders = "N/A";
    this.lastURL = "N/A";
    this.name = "";
    this.password = "";

    var userCtrl = this;

    // Check to see if current user is logged in
    if($cookies.get('userid') > 0) {
      this.isLoggedIn = true;
    }

    this.login = function() {
      // send the current values and see what's up.

      var data = {
        "user": this.name,
        "password": this.password
      };

      $http.post(this.targetUrl, data).success(this.login_success).error(this.login_failure);
    }

    this.reset_params = function() {
      this.parameters = [];
    }

    this.login_success = function(data, status, headers, config){
      userCtrl.lastHeaders = headers();
      userCtrl.lastHeaders.url = config.url;
      userCtrl.lastHeaders.status = status;
      userCtrl.cookies = [];
      var allCookies = $cookies.getAll();
      for (var key in allCookies){
        if (allCookies.hasOwnProperty(key)){
          c = {"name": key, "value": allCookies[key]};
          userCtrl.cookies.push(c);
          if (key == 'userid' && allCookies[key] > 0 ){
            userCtrl.isLoggedIn = true;
          }
        }
      }
    }

    this.login_failure = function(data, status, headers, config) {
      alert("Login Failed");
      userCtrl.lastHeaders = headers();
      userCtrl.lastHeaders.status = status;
    }

  }]);

  app.directive("historiaContent", function() {
    return {
      restrict: "E",
      templateUrl: "/historia/files/html/main_content.html",
    };
  });

  app.directive('welcomePage', function() {
    return {
      restrict: 'E',
      templateUrl: '/historia/files/html/welcome.html'
    }
  });

  app.directive('testPage', function() {
    return {
      restrict: 'E',
      templateUrl: '/historia/files/html/test_form.html'
    }
  });

  app.directive('userLoginPage', function() {
    return {
      restrict: 'E',
      templateUrl: '/historia/files/html/login.html'
    }
  });


})();
