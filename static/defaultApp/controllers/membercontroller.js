
(function () {
    var injectParams = ['$scope', '$location', '$routeParams',
                        '$timeout','ngDialog', 'config', 'dataService','toaster','displayModel','MyCache'];

    var MemberController = function ($scope, $location, $routeParams,
                                           $timeout, ngDialog,config, dataService,toaster,displayModel,MyCache) {
        var vm = this;
        vm.initdata={
            display:'day',
            start_time:'',
            end_time:''
            };
        vm.member={};

    //doughnut-report-支付方式
        vm.getmember = function(display) {
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
            dataService.getmember(vm.initdata)
            .then(function (data) {
                if (data.errcode == 1){
                    toaster.pop('error',"访问失败","没有权限查看报表")
                }
            	vm.member = data;
                  $scope.labels2 = ["活跃会员", "普通会员","沉睡会员"];
                  $scope.data2 = [vm.member.active_member_cnt, vm.member.normal_member_cnt,vm.member.sleep_member_cnt];
                  $scope.colors2 = ['#3684F1','#15B9F3','#02E5F2'];
                  $scope.labels = ["储值余额", "卡内项目"];
                  $scope.data = [vm.member.total_amount , vm.member.consume_amount];
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
            displayModel.get_data = vm.getmember;
            vm.getmember()
        }

        init();
    };

    MemberController.$inject = injectParams;
    angular.module('dashboardApp').controller('MemberController', MemberController);

}());