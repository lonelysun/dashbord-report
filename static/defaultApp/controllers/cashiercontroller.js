
(function () {
    var injectParams = ['$scope', '$location', '$routeParams',
                        '$timeout','ngDialog', 'config', 'dataService','toaster','displayModel','MyCache'];

    var CashierController = function ($scope, $location, $routeParams,
                                           $timeout, ngDialog,config, dataService,toaster,displayModel,MyCache) {
        var vm = this;
        vm.initdata={
            display:'day',
            start_time:'',
            end_time:''
            };
        vm.cashierdata={};

    //doughnut-report-支付方式
        vm.getcashier =  function(display) {
            if (display) {
                vm.initdata.display = display;
                MyCache.put('display',display);
            }else if(MyCache.get('display')&&MyCache.get('display')!='none'){
                vm.initdata.display = MyCache.get('display');
            }
            if (MyCache.get('role')){
                vm.initdata.start_time = MyCache.get('role').start_time;
                vm.initdata.end_time = MyCache.get('role').end_time;
                vm.initdata.display = display;
            }
            dataService.getcashier(vm.initdata)
            .then(function (data) {
                if (data.errcode == 1){
                    toaster.pop('error',"访问失败","没有权限查看报表")
                }
            	vm.cashierdata = data;
                var labels2_name =[];
                var labels2_amount =[];
                var all_color = ['#5a72db','#3b87ee','#28baf0','#28e5f0','#5fedb2','#80ed5f','#ede85f','#ed765f','#eb5fed','#8b5adb'];
                $scope.colors = [];
                vm.cashierdata.all_pay = data.all_amount;
                for (pay in data.pay_way){
                    labels2_name.push(data.pay_way[pay].name);
                    labels2_amount.push(data.pay_way[pay].amount);
                    $scope.colors.push(all_color[pay])
                }
                $scope.labels2 = labels2_name;
                $scope.data2 = labels2_amount;
                $scope.options2 = {'percentageInnerCutout':80};

                vm.isLoad=true;
                $timeout(function () {
                    vm.busy=false;
                }, 500);
            }, function (error) {
            	toaster.pop('error', "处理失败", "很遗憾处理失败，由于网络原因无法连接到服务器！");
            });
        };




        function init() {
            displayModel.get_data = vm.getcashier;
            vm.getcashier()
        }

        init();
    };

    CashierController.$inject = injectParams;
    angular.module('dashboardApp').controller('CashierController', CashierController);

}());