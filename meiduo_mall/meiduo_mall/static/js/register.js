// ES6语法
// 创建一个vue对象
let vm = new Vue({
    el: '#app',//通过ID选择器找到绑定的HTML内容
    data: { // 数据对象
        // v-model
        username: "",
        password: "",
        password2: "",
        mobile: "",
        allow: "",
        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        //error_message
        error_name_message: "",
        error_mobile_message: "",
    },
    methods: {//定义和实现事件方法
        // 校验用户名
        check_username() {
            //   用户名是5-20字符,[a-zA-Z0-9_-]
            //    定义正则
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            //    使用正则匹配用户名数据
            if (re.test(this.username)) {
                // 匹配成功不展示错误信息
                this.error_name = false;
            } else {
                // 匹配失败展示错误信息
                this.error_name_message = "请输入5～20个字符的用户名";
                this.error_name = true;
            }
        },
        // 校验密码
        check_password() {
            let re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },
        // 校验确认密码
        check_password2() {
            if (this.password != this.password2) {
                this.error_password2 = true;
            } else {
                this.error_password2 = false;
            }
        },
        // 校验手机号
        check_mobile() {
            let re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile_message = "您输入的手机号格式不正确";
                this.error_mobile = true;
            }
        },
        // 校验是否勾选协议
        check_allow() {
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },
        // 监听表单提交事件
        on_submit() {

        },
    }

});