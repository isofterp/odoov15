/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { symmetricalDifference } from "@web/core/utils/arrays";
import { session } from "@web/session";

function parseBranchIds(cidsFromHash) {
    const cids = [];
    if (typeof cidsFromHash === "string") {
        cids.push(...cidsFromHash.split(",").map(Number));
    } else if (typeof cidsFromHash === "number") {
        cids.push(cidsFromHash);
    }
    return cids;
}

function computeAllowedBranchIds(cids) {
    const { user_branches } = session;
    //console.log(session.allowed_branch_ids);
    let allowedBranchIds = cids || [];
    const availableBranchesFromSession = session.user_companies.user_branches;
    //const notReallyAllowedBranches = allowedBranchIds.filter(
    //    (branch_id) => !(branch_id in availableBranchesFromSession)
    //);

    //if (!allowedBranchIds.length || notReallyAllowedBranches.length) {
    //    allowedBranchIds = [user_branches.current_branch];
    //}

    const {branch_id, branch_name}  = session.user_companies.allowed_branches
    //console.log(typeof session.user_companies.allowed_branch_ids)

    //console.log( branch_id, branch_name);
    return session.user_companies.allowed_branches;
    //return session.user_companies.
}

export const branchService = {
    dependencies: ["user", "router", "cookie"],
    start(env, { user, router, cookie }) {
        let cids;
        if ("cids" in router.current.hash) {
            cids = parseBranchIds(router.current.hash.cids);
        } else if ("cids" in cookie.current) {
            cids = parseBranchIds(cookie.current.cids);
        }
        let allowedBranchIds = computeAllowedBranchIds(cids);
        console.log(allowedBranchIds)

        const stringCIds = allowedBranchIds.join(",");

        router.replaceState({ cids: stringCIds }, { lock: true });
        cookie.setCookie("cids", stringCIds);

        user.updateContext({ allowed_branch_ids: allowedBranchIds });
        const availableBranches = session.user_companies.user_branches;

        return {
            availableBranches,
            get allowedBranchIds() {
                return allowedBranchIds.slice();
            },
            get currentBranch() {
                return availableBranches[allowedBranchIds[0]];
            },
            setBranches(mode, ...branchIds) {
                // compute next company ids
                let nextBranchIds;
                if (mode === "toggle") {
                    nextBranchIds = symmetricalDifference(allowedBranchIds, branchIds);
                } else if (mode === "loginto") {
                    const branchId = branchIds[0];
                    if (allowedBranchIds.length === 1) {
                        // 1 enabled company: stay in single company mode
                        nextBranchIds = [branchId];
                    } //else {
                        // multi company mode
                      //  nextBranchIds = [
                       //     branchId,
                         //   ...allowedBranchIds.filter((branch_id) => id !== branchId),
                       // ];
                   // }
                }
                nextBranchIds = nextBranchIds.length ? nextBranchIds : [branchIds[0]];

                // apply them
                router.pushState({ cids: nextBranchIds }, { lock: true });
                cookie.setCookie("cids", nextBranchIds);
                browser.setTimeout(() => browser.location.reload()); // history.pushState is a little async
            },
        };
    },
};

registry.category("services").add("branch", branchService);
