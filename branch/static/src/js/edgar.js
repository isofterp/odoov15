/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var ajax = require('web.ajax');
var rpc = require('web.rpc');
var utils = require('web.utils');
var request
var _t = core._t;

var SwitchBranchMenu = Widget.extend({
    template: 'SwitchBranchMenu',
    events: {
        'click .dropdown-item1[data-menu]': '_onSwitchBranchClick',
        'keydown .dropdown-item1[data-menu]': '_onSwitchBranchClick',

    },
    init: function () {
        this._super.apply(this, arguments);
        this.isMobile = config.device.isMobile;
        this._onSwitchBranchClick = _.debounce(this._onSwitchBranchClick, 1500, true);
    },


    _onSwitchBranchClick: function (ev) {
        console.Log("On click is running")
        if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        var dropdownItem = $(ev.currentTarget);
        var dropdownMenu = dropdownItem;
        var branchID = dropdownItem.data('branch-id');
        var allowed_branch_ids = this.allowed_branch_ids;
        if (dropdownItem.find('.fa-square-o').length) {
            // 1 enabled company: Stay in single company mode
            if (this.allowed_branch_ids.length === 1) {
                if (this.isMobile) {
                    dropdownMenu = dropdownMenu.parent();
                }
                dropdownMenu.find('.fa-check-square').removeClass('fa-check-square').addClass('fa-square-o');
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
                allowed_branch_ids = [branchID];
            } else { // Multi company mode
                allowed_branch_ids.push(branchID);
                dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
            }
        }
        $(ev.currentTarget).attr('aria-pressed', 'true');
        session.setBranch(branchID, allowed_branch_ids);

        ajax.jsonRpc('/set_brnach', 'call', {
                    'BranchID':  branchID,
            })
        ajax.jsonRpc('/set_brnach', 'call', {
                    'BranchID':  branchID,
            })
    },

    _onToggleBranchClick: function (ev) {
        if (ev.type == 'keydown' && ev.which != $.ui.keyCode.ENTER && ev.which != $.ui.keyCode.SPACE) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        var dropdownItem = $(ev.currentTarget).parent();
        var branchID = dropdownItem.data('branch-id');
        var allowed_branch_ids = this.allowed_branch_ids;
        var current_branch_id = allowed_branch_ids[0];
        if (dropdownItem.find('.fa-square-o').length) {
            allowed_branch_ids.push(branchID);
            dropdownItem.find('.fa-square-o').removeClass('fa-square-o').addClass('fa-check-square');
            $(ev.currentTarget).attr('aria-checked', 'true');
        } else {
            allowed_branch_ids.splice(allowed_branch_ids.indexOf(branchID), 1);
            dropdownItem.find('.fa-check-square').addClass('fa-square-o').removeClass('fa-check-square');
            $(ev.currentTarget).attr('aria-checked', 'false');
        }
        session.setBranch(current_branch_id, allowed_branch_ids);
    },
});

SystrayMenu.Items.push(SwitchBranchMenu);
return SwitchBranchMenu;