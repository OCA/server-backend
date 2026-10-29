// Copyright 2025 Akretion (http://www.akretion.com).
// @author Florian Mounier <florian.mounier@akretion.com>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {useChildRef, useService} from "@web/core/utils/hooks";

import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownGroup} from "@web/core/dropdown/dropdown_group";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {useCommand} from "@web/core/commands/command_hook";
import {useDropdownState} from "@web/core/dropdown/dropdown_hooks";
import {user} from "@web/core/user";

export class SwitchProfileMenu extends Component {
    static components = {Dropdown, DropdownItem, DropdownGroup};
    static props = [];
    static template = "base_user_role_profile.switchProfileMenu";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dropdown = useDropdownState();

        useCommand(_t("Switch Profile"), () => this.dropdown.open(), {
            hotkey: "alt+shift+p",
        });

        this.containerRef = useChildRef();
        this.navigationOptions = {
            hotkeys: {
                space: (index, items) => {
                    if (!items[index]) {
                        return;
                    }
                    if (items[index].el.classList.contains("o_switch_profile_item")) {
                        const profileId = parseInt(
                            items[index].el.dataset.profileId,
                            10
                        );
                        this.switchToProfile(profileId);
                        this.dropdown.close();
                    }
                },
                enter: (index, items) => {
                    if (!items[index]) {
                        return;
                    }
                    if (items[index].el.classList.contains("o_switch_profile_item")) {
                        const profileId = parseInt(
                            items[index].el.dataset.profileId,
                            10
                        );
                        this.switchToProfile(profileId);
                        this.dropdown.close();
                    }
                },
            },
        };
    }

    get currentProfile() {
        return session.user_profiles?.current_profile;
    }

    get profiles() {
        return session.user_profiles?.allowed_profiles || [];
    }

    get isEnabled() {
        return this.profiles.length > 1;
    }

    async switchToProfile(profileId) {
        if (profileId === this.currentProfile) {
            return;
        }
        const action = await this.orm.call("res.users", "action_profile_change", [
            user.userId,
            {profile_id: profileId},
        ]);
        if (action) {
            this.action.doAction(action);
        }
    }
}

export const systrayItem = {
    Component: SwitchProfileMenu,
};

registry
    .category("systray")
    .add("base_user_role_profile.switchProfileMenu", systrayItem, {sequence: 5});
