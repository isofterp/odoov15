odoo.define('lv_ord.CartMenu', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var SystrayMenu = require('web.SystrayMenu');
    var core = require('web.core');
    var Dialog = require('web.Dialog');

    var _t = core._t;

    var cart_menu = Widget.extend({
        template:'lv_ord.CartMenu',
        events: {
            "click #cart_menu_icon": "toggle_cart",
            "click #cart_menu_times": "toggle_cart",
            "click #id_empty_cart": "emptyCart",
            "click #edit_item": "editItem",
            "click #remove_item": "removeItem",
            "click #copy_item": "copyItem",
            "change #checkout_all": "checkoutAll",
            "click #checkout_cart": "checkoutCart"
        },
        start: function () {
            var self = this;
            return this._super(...arguments).then(function () {
                self.get_cart_params();
            });
        },

        toggle_cart: function (event) {
            var cart_menu = document.getElementById('cart_menu');
            if (cart_menu.getAttribute('cart-menu') == "false") {
                cart_menu.classList.add("show");
                document.getElementById('cart_menu_dropdown').style.display = 'block';
                cart_menu.setAttribute('cart-menu', "true");
            }
            else {
                cart_menu.classList.remove("show");
                document.getElementById('cart_menu_dropdown').style.display = 'none';
                cart_menu.setAttribute('cart-menu', "false");
            }

        },

        get_cart_params: function (event) {
            rpc.query({
               model: 'lv.ord.corder',
               method: 'get_cart_params',
               args: [],
           }).then(function(cart_params) {
                document.getElementById('id_cart_count').innerHTML = cart_params['count'];
                document.getElementById('cart_chain_name').innerHTML = cart_params['chain'];
                document.getElementById('cart_customer_name').innerHTML = cart_params['customer'];
                document.getElementById('cart_table').innerHTML = cart_params['cart_table'];
           });
        },

        editItem: function (event) {
            location.href = "/cart/edit-item/" + event.currentTarget.attributes[4].value;
        },

        removeItem: function (event) {
             Dialog.confirm(this, _t("Are you sure you want to remove this line from your order?"), {
                 confirm_callback:  () => rpc.query({
                       model: 'lv.ord.corder',
                       method: 'get_cart_params',
                       args: [],
                   }).then(function(cart_params) {
                         var table = document.getElementById('cart_table')
                         location.href = "/cart/remove-item/" + event.currentTarget.attributes[4].value;
                 }),
             });
        },

        copyItem: function (event) {
             Dialog.confirm(this, _t("Do you want to duplicate this order line?"), {
                 confirm_callback:  () => rpc.query({
                       model: 'lv.ord.corder',
                       method: 'get_cart_params',
                       args: [],
                   }).then(function(cart_params) {
                         location.href = "/cart/copy-item/" + event.currentTarget.attributes[4].value;
                 }),
             });
        },

        emptyCart: function (event) {
             Dialog.confirm(this, _t("Are you sure you want to empty your cart?"), {
                 confirm_callback:  () => rpc.query({
                       model: 'lv.ord.corder',
                       method: 'get_cart_params',
                       args: [],
                   }).then(function(cart_params) {
                        location.href = "/cart/empty-cart/" + cart_params['corder_id'];
                 }),
             });
        },

        checkoutAll: function (event) {
            var checkout_all = document.getElementById("checkout_all").checked;
            var items = document.getElementsByClassName("checkout_item");
            for (var i = 0; i < items.length; i++) {
                items[i].checked = checkout_all;
            }
        },

        checkoutCart: function (event) {
            var wo_ids = "";
            var items = document.getElementsByClassName("checkout_item");
            for (var i = 0; i < items.length; i++) {
                if(items[i].checked)
                    wo_ids += items[i].attributes[3].value + ",";
            }
            //wo_ids = wo_ids.replace(/,\s*$/, "")
            if(wo_ids.length <= 0) {
                Dialog.alert(self, _t("Please select the items that you want to checkout!"), {
                    title: _t('Checkout'),
                });
                return false;
            }
            location.href = "/cart/checkout-cart/" + wo_ids;
        },

    });
    cart_menu.prototype.sequence = 1;
    SystrayMenu.Items.push(cart_menu);
});
