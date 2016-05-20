(function () {

    var injectParams = ['$http', '$q'];

    var productsFactory = function ($http, $q) {
        var serviceBase = '/dashboard/',
            factory = {};

        //收银统计
        factory.getcashier = function (display) {

            return $http.get(serviceBase + 'getcashier',{
                params:display
            }).then(function(results) {
     				return results.data;
     			});
        };

        //营业统计
        factory.getsale = function (display) {

            return $http.get(serviceBase + 'getsale',{
                params:display
            }).then(function(results) {
     				return results.data;
     			});
        };

        //会员统计
        factory.getmember = function (display) {

            return $http.get(serviceBase + 'getmember',{
                params:display
            }).then(function(results) {
     				return results.data;
     			});
        };

        return factory;
    };

    productsFactory.$inject = injectParams;

    angular.module('dashboardApp').factory('shopService', productsFactory);

}());