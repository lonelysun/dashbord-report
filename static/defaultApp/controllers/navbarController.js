(function () {

    var injectParams = ['$scope', '$location', 'config','displayModel','MyCache','ngDialog'];
    var NavbarController = function ($scope, $location, config,displayModel,MyCache,ngDialog) {
        var vm = this;

        vm.clicked = 'cashier';
        vm.display = 'day';
        vm.bottom = 'cashier';

        //控制导航栏显示
        vm.setDisplay = function(display){
            if (display!='none'){
                MyCache.remove('role');
                vm.display = display;
            }
            displayModel.get_data(display);
        };
        vm.setBottom = function(bottom){
            vm.bottom = bottom;
        };
        vm.role = function () {
            angular.selectRole()
        };
        angular.selectRole = function(){

            $scope.modalOptions = {
                'start_time':'',
                'end_time':''
            };

            ngDialog.openConfirm({
                template:'/born_dashboard/static/defaultApp/partials/selectrole.html',
                className: 'ngdialog',
                scope: $scope
            }).then(function (data) {
                if(data == 'ok'){
                   var yyyy = $scope.modalOptions.start_time.getFullYear().toString();
                   var mm = ($scope.modalOptions.start_time.getMonth()+1).toString(); // getMonth() is zero-based
                   var dd  = $scope.modalOptions.start_time.getDate().toString();
                   var time_date = yyyy +'-'+ (mm[1]?mm:"0"+mm[0]) +'-'+ (dd[1]?dd:"0"+dd[0])+' '+'00:00:00'; // padding
                    $scope.modalOptions.start_time = time_date
                   var end_yyyy = $scope.modalOptions.end_time.getFullYear().toString();
                   var end_mm = ($scope.modalOptions.end_time.getMonth()+1).toString(); // getMonth() is zero-based
                   var end_dd  = $scope.modalOptions.end_time.getDate().toString();
                   var end_time_date = end_yyyy +'-'+ (end_mm[1]?end_mm:"0"+end_mm[0]) +'-'+ (end_dd[1]?end_dd:"0"+end_dd[0])+' '+'23:59:59'; // padding
                    $scope.modalOptions.end_time = end_time_date;
                    MyCache.put('role',$scope.modalOptions);
                    vm.setDisplay('none')
                }
            })
        };

        vm.menu = function(){
            window.location.href = 'bornhr://pop';
        }
    };

    NavbarController.$inject = injectParams;

    angular.module('dashboardApp').controller('NavbarController', NavbarController);

}());
function selectRole(){
    angular.selectRole();
}
