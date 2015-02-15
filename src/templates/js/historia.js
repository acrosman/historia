(function () {
  
  var app = angular.module('historia', []);
  
  app.controller('historiaController', function() {
    this.tab = 1;

    this.isSet = function(checkTab) {
      return this.tab === checkTab;
    };

    this.setTab = function(activeTab) {
      this.tab = activeTab;
    };
    
  });
  
  app.controller('SubmissionController', ['$http',function($http){
    
    this.parameters = [];
    this.targetUrl = "/historia";
    this.method = "";
    this.lastResponse = {};
    this.lastHeaders = "N/A";
    this.lastURL = "N/A";
    
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
    }
  
  }]);
  
  app.controller('ParameterController', function(){
    
    this.parameter = {}
    
    this.addParameter = function(submission) {
      submission.parameters.push(this.parameter);
      this.parameter = {};
    };
    
  });
  
  
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
  
  
})();