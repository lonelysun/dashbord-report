
(function () {
    var injectParams = ['$scope', '$location', '$routeParams',
                        '$timeout','ngDialog', 'config', 'dataService','toaster','displayModel','MyCache'];

    var SaleController = function ($scope, $location, $routeParams,
                                           $timeout, ngDialog,config, dataService,toaster,displayModel,MyCache) {
        var vm = this;
        vm.initdata={
            display:'day',
            start_time:'',
            end_time:''
            };
        vm.sale={};

        vm.getsale = function(display) {

            if (display) {
                vm.initdata.display = display;
                MyCache.put('display',display);
            }else if(MyCache.get('display')&&MyCache.get('display')!='none'){
                vm.initdata.display = MyCache.get('display');
            }
            if (MyCache.get('role')){
                vm.initdata.start_time = MyCache.get('role').start_time;
                vm.initdata.end_time = MyCache.get('role').end_time;
            }
            dataService.getsale(vm.initdata)
            .then(function (data) {
                if (data.errcode == 1){
                    toaster.pop('error',"访问失败","没有权限查看报表")
                }
            	vm.sale = data;
                  $scope.labels2 = ["销售额", "办卡/充值","欠款","还款","退款"];
                  $scope.data2 = [vm.sale.sale_amount, vm.sale.recharge_amount,vm.sale.arrears_amount,vm.sale.repayment_amount,vm.sale.refund_amount];
                  $scope.colors2 = ['#596FDE','#3684F1','#15B9F3','#02E5F2','#57EEB1'];
                  $scope.labels = ["产品消售额", "项目消耗额"];
                  $scope.data = [vm.sale.product_consume_amount, vm.sale.item_consume_amount];
                  $scope.colors = ['#15B9F3','#02E5F2'];
                  $scope.options = {'percentageInnerCutout':80};

                vm.isLoad=true;
                $timeout(function () {
                    vm.busy=false;
                }, 500);
            }, function (error) {
            	toaster.pop('error', "处理失败", "很遗憾处理失败，由于网络原因无法连接到服务器！");
            });
        };




        function init() {
            displayModel.get_data = vm.getsale;
            vm.getsale()
        }

        init();
    };

    SaleController.$inject = injectParams;
    angular.module('dashboardApp').controller('SaleController', SaleController);

}());