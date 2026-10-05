/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class OtmGuestReceptionDashboard extends Component {
    static template = "guest_tracking.ReceptionDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ kpi: {}, visits: [], loading: true });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.loading = true;
        const data = await this.orm.call("otm.guest.visit", "get_reception_dashboard_data", []);
        this.state.kpi = data.kpi;
        this.state.visits = data.visits;
        this.state.loading = false;
    }

    async onStartMeeting(id) {
        await this.orm.call("otm.guest.visit", "action_start_meeting", [[id]]);
        await this.loadData();
    }

    async onCompleteVisit(id) {
        await this.orm.call("otm.guest.visit", "action_complete_visit", [[id]]);
        await this.loadData();
    }

    async onCancelVisit(id) {
        await this.orm.call("otm.guest.visit", "action_cancel_visit", [[id]]);
        await this.loadData();
    }

    openVisit(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "otm.guest.visit",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openQuickAction(resModel, viewMode) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: resModel,
            views: viewMode === "form" ? [[false, "form"]] : [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("otm_guest_reception_dashboard", OtmGuestReceptionDashboard);


export class OtmGuestAnalyticsDashboard extends Component {
    static template = "guest_tracking.AnalyticsDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            kpi: {}, by_branch: [], by_purpose: [], by_course: [], by_status: [],
            loading: true, range: "this_month",
        });
        onWillStart(() => this.loadData());
    }

    _dateBounds(range) {
        const today = new Date();
        const fmt = (d) => d.toISOString().slice(0, 10);
        let from, to;
        const y = today.getFullYear(), m = today.getMonth(), d = today.getDate();
        if (range === "today") {
            from = to = fmt(today);
        } else if (range === "yesterday") {
            const yst = new Date(y, m, d - 1);
            from = to = fmt(yst);
        } else if (range === "this_week") {
            const day = today.getDay() || 7;
            from = fmt(new Date(y, m, d - day + 1));
            to = fmt(today);
        } else if (range === "this_month") {
            from = fmt(new Date(y, m, 1));
            to = fmt(today);
        } else if (range === "last_month") {
            from = fmt(new Date(y, m - 1, 1));
            to = fmt(new Date(y, m, 0));
        } else {
            from = false;
            to = false;
        }
        return [from, to];
    }

    async loadData() {
        this.state.loading = true;
        const [from, to] = this._dateBounds(this.state.range);
        const data = await this.orm.call("otm.guest.visit", "get_analytics_dashboard_data", [from, to]);
        Object.assign(this.state, data, { loading: false });
    }

    async onRangeChange(ev) {
        this.state.range = ev.target.value;
        await this.loadData();
    }
}

registry.category("actions").add("otm_guest_analytics_dashboard", OtmGuestAnalyticsDashboard);
