odoo.define('web.SwitchProfileMenu', function(require) {
    "use strict";

    var config = require('web.config');
    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget')
    var _t = core._t;

    var SwitchProfileMenu = Widget.extend({
        template: 'SwitchProfileMenu',
        events: {
            'click .dropdown-item[data-menu]': '_onClick',
        },

        init: function() {
            this._super.apply(this, arguments);
            this.isMobile = config.device.isMobile;
            this._onClick = _.debounce(this._onClick, 1500, true);
        },

        willStart: function() {
            return session.user_profiles ? this._super() : $.Deferred().reject();
        },

        start: function() {
            var profilesList = '';
            if (this.isMobile) {
                profilesList = '<li class="bg-info">' +
                    _t('Tap on the list to change profile') + '</li>';
            } else {
                this.$('.oe_topbar_name').text(session.user_profiles.current_profile[1]);
            }
            _.each(session.user_profiles.allowed_profiles, function(profile) {
                var a = '';
                if (profile[0] == session.user_profiles.current_profile[0]) {
                    a = '<i class="fa fa-check mr8"></i>';
                } else {
                    a = '<span style="margin-right: 24px;"/>';
                }
                profilesList += '<a role="menuitem" href="#" class="dropdown-item" data-menu="profile" data-profile-id="' +
                    profile[0] + '">' + a + profile[1] + '</a>';
            });
            this.$('.dropdown-menu').html(profilesList);
            return this._super();
        },

        _onClick: function(ev) {
            var self = this;
            ev.preventDefault();
            var profileID = $(ev.currentTarget).data('profile-id');
            // We use this instead of the location.reload() because permissions change
            // and we might land on a menu that we don't have permissions for. Thus it
            // is cleaner to reload any root menu
            this._rpc({
                    model: 'res.users',
                    method: 'action_profile_change',
                    args: [
                        [session.uid], {
                            'profile_id': profileID
                        }
                    ],
                })
                .done(
                    function(result) {
                        self.trigger_up('do_action', {
                            action: result,
                        })
                    }
                )
        },
    });

    SystrayMenu.Items.push(SwitchProfileMenu);

    return SwitchProfileMenu;

});
