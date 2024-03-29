/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";
import { symmetricalDifference } from "@web/core/utils/arrays";

const { Component, hooks } = owl;
const { useState } = hooks;

export class SwitchBranchMenu extends Component {
    setup() {
        this.branchService = useService("branch");
        this.currentBranch = this.branchService.currentBranch;
        this.state = useState({ branchesToToggle: [] });
    }

    toggleBranch(branchId) {
        this.state.branchesToToggle = symmetricalDifference(this.state.branchesToToggle, [
            branchId,
        ]);
        browser.clearTimeout(this.toggleTimer);
        this.toggleTimer = browser.setTimeout(() => {
            this.branchService.setBranches("toggle", ...this.state.branchesToToggle);
        }, this.constructor.toggleDelay);
    }

    logIntoBranch(branchId) {
        browser.clearTimeout(this.toggleTimer);
        this.branchService.setBranches("loginto", branchId);
    }

    get selectedBranches() {
        return symmetricalDifference(
            this.branchService.allowedBranchIds,
            this.state.branchesToToggle
        );
    }
}
SwitchBranchMenu.template = "branch.SwitchBranchMenu";
SwitchBranchMenu.toggleDelay = 1000;

export const systrayItem = {
    Component: SwitchBranchMenu,
    isDisplayed(env) {
        const { availableBranches } = env.services.branch;
        return Object.keys(availableBranches).length > 1;
    },
};

registry.category("systray").add("availableBranches", systrayItem, { sequence: 1 });
