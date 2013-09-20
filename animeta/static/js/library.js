moment.lang('ko');

var App = Ember.Application.create({
    rootElement: '#app-root',
    LOG_TRANSITIONS: true
});
App.USERNAME = USERNAME;
App.CURRENT_USERNAME = CURRENT_USERNAME;

if (Modernizr.history) {
    App.Router.reopen({
        location: 'history',
        rootURL: '/users/' + App.USERNAME + '/'
    });
}

App.Router.map(function() {
    this.resource('library', {path: '/'}, function() {
        this.route('item', {path: '/items/:item_id'});
    });
});

Ember.Model.reopenClass({
    camelizeKeys: true
});

App.APIAdapter = Ember.RESTAdapter.extend({
    buildURL: function(klass, id) {
        var urlRoot = '/api/v2' + Ember.get(klass, 'url');
        if (!urlRoot) { throw new Error('Ember.RESTAdapter requires a `url` property to be specified'); }
        if (!Ember.isEmpty(id)) {
            return urlRoot + "/" + id;
        } else {
            return urlRoot;
        }
    }
});

var UnixTimestamp = {
    deserialize: function(value) {
        return new Date(value * 1000);
    },

    serialize: function(date) {
        return date.getTime() / 1000;
    }
};

var attr = Ember.attr, hasMany = Ember.hasMany, belongsTo = Ember.belongsTo;

App.User = Ember.Model.extend({
    id: attr(),
    username: attr(),
    items: hasMany('App.LibraryItem', {key: 'items', embedded: true})
});
App.User.url = '/users';
App.User.primaryKey = 'username';
App.User.adapter = App.APIAdapter.create();

App.LibraryItem = Ember.Model.extend({
    id: attr(),
    title: attr(),
    progress: attr(),
    status: attr(),
    updatedAt: attr(UnixTimestamp),
    user: belongsTo('App.User', {key: 'user_id'}),
    updates: hasMany('App.Update', {key: 'updates', embedded: true}),

    isWatching: function() {
        return this.get('status') == 'watching';
    }.property('status'),

    saveStatus: function() {
        return this.constructor.adapter.saveStatus(this);
    },

    statusText: function() {
        return App.STATUS_TEXTS[this.get('status')];
    }.property('status')
});
App.LibraryItem.url = '/items';
App.LibraryItem.adapter = App.APIAdapter.extend({
    saveStatus: function(record) {
        var get = Ember.get;
        var primaryKey = get(record.constructor, 'primaryKey'),
        url = this.buildURL(record.constructor, get(record, primaryKey)),
        self = this;

        return Ember.$.ajax(url, {type: 'PUT', data: {status: record.get('status')}}).then(function(data) { // TODO: Some APIs may or may not return data
            self.didSaveRecord(record, data);
            return record;
        });
    }
}).create();

App.Update = Ember.Model.extend({
    id: attr(),
    progress: attr(),
    status: attr(),
    updatedAt: attr(UnixTimestamp),
    comment: attr(),
    item: belongsTo('App.LibraryItem', {key: 'item_id'}),

    progressSuffix: function() {
        return this.get('progress').match(/(^$)|([0-9]$)/) ? '화' : '';
    }.property('progress'),

    isWatching: function() {
        return this.get('status') == 'watching';
    }.property('status'),

    hasProgress: function() {
        return this.get('progress').length > 0;
    }.property('progress'),

    progressText: function() {
        var p = this.get('progress');
        if (p.match(/[0-9]$/))
            p += '화';
        return p;
    }.property('progress'),

    statusText: function() {
        return App.STATUS_TEXTS[this.get('status')];
    }.property('status')
});
App.Update.url = '/updates';
App.Update.adapter = App.APIAdapter.create();

App.LibraryRoute = Ember.Route.extend({
    model: function() {
        return App.User.fetch(App.USERNAME).then(function(user) {
            return user.get('items');
        });
    }
});

function getDateHeader(nativeDate) {
    var date = moment(nativeDate);
    var today = moment().startOf('day');
    var days = today.diff(date, 'days');
    if (days <= 60) {
        if (days < 1)
            return '오늘';
        else if (days < 2)
            return '어제';
        else if (days < 3)
            return '그저께';
        else if (days < 4)
            return '그끄저께';
        else if (date.isSame(today, 'week'))
            return '이번 주';
        else if (date.isSame(today.clone().subtract('week', 1), 'week'))
            return '지난 주';
        else if (date.isSame(today, 'month'))
            return '이번 달';
        else if (date.isSame(today.clone().subtract('month', 1), 'month'))
            return '지난 달';
    }
    return date.format('YYYY/MM');
}

App.LibraryController = Ember.ArrayController.extend({
    sortProperties: ['updatedAt'],
    sortAscending: false,
    sectionedContents: function() {
        var sections = [], section = null;
        this.forEach(function(item) {
            var h = getDateHeader(item.get('updatedAt'));
            if (!section || section.header != h) {
                if (section)
                    sections.push(section);
                section = { header: h, items: [] };
            }
            section.items.push(item);
        });
        if (section.items.length > 0)
            sections.push(section);
        return sections;
    }.property('@each.updatedAt'),

    open: function(item) {
        this.close();
        this.set('openItem', item);
        item.set('open', true);
    },

    close: function() {
        var openItem = this.get('openItem');
        if (openItem) {
            openItem.set('open', false);
            this.set('openItem', null);
        }
    }
});

App.STATUS_TEXTS = {
    watching: '보는 중',
    finished: '완료',
    suspended: '중단',
    interested: '관심'
};

App.ItemStatusComponent = Ember.Component.extend({
    tagName: 'span',
    classNames: ['status'],

    isWatching: function() {
        return this.get('status') == 'watching';
    }.property('status'),

    hasProgress: function() {
        return this.get('progress').length > 0;
    }.property('progress'),

    progressText: function() {
        var p = this.get('progress');
        if (p.match(/[0-9]$/))
            p += '화';
        return p;
    }.property('progress'),

    statusText: function() {
        return App.STATUS_TEXTS[this.get('status')];
    }.property('status')
});

App.LibraryItemRoute = Ember.Route.extend({
    model: function(params) {
        return App.LibraryItem.fetch(params.item_id);
    },

    setupController: function(controller, model) {
        model.reload();
        this.controllerFor('library').open(model);
        //controller.set('model', model);
    },

    renderTemplate: function() {
        // DO NOTHING
    },

    deactivate: function() {
        this.controllerFor('library').close();
    }
});

App.LibraryItemController = Ember.ObjectController.extend({
    canEdit: function() {
        return App.USERNAME == App.CURRENT_USERNAME;
    }.property(),

    newUpdate: function() {
        var progress = this.get('progress');
        var m = progress.match(/([0-9]+)$/);
        if (m) {
            var n = parseInt(m[1], 10);
            n++;
            progress = progress.substr(0, m.index) + n;
        }
        return App.Update.create({
            item: this.get('model'),
            progress: progress
        });
    }.property('progress'),

    statusChanged: function() {
        // Check if the value is really changed
        // to prevent accidental save request.
        var prev = this.get('prevStatus'),
            changed = this.get('status');
        this.set('prevStatus', changed);
        if (prev == null || prev == changed)
            return;
        this.get('model').saveStatus();
    }.observes('status'),

    actions: {
        saveUpdate: function() {
            var self = this;
            this.get('newUpdate').save().then(function(update) {
                // XXX: expensive
                self.get('model').reload();
            });
        }
    }
});

App.LibraryItemView = Ember.View.extend({
    didInsertElement: function() {
        var offset = this.$().offset().top;
        var viewportHeight = Ember.$(window).height();
        var viewportBegin = Ember.$(document).scrollTop();
        var viewportEnd = viewportBegin + viewportHeight;
        var margin = viewportHeight / 4;
        if (offset < viewportBegin || offset > viewportEnd) {
            Ember.$(document).scrollTop(offset - margin);
        }
    }
});

App.UpdateController = Ember.ObjectController.extend({
    needs: 'libraryItem',

    shouldShowStatus: function() {
        var s = this.get('status');
        return s && s != 'watching';
    }.property('status', 'progress'),

    progressText: function() {
        if (this.get('hasProgress'))
            return this.get('progress') + this.get('progressSuffix');
        return App.STATUS_TEXTS.watching;
    }.property('progress', 'progressSuffix'),

    updatedAtFromNow: function() {
        return moment(this.get('updatedAt')).fromNow();
    }.property('updatedAt'),

    canEdit: Ember.computed.alias('controllers.libraryItem.canEdit'),

    hasComment: function() {
        return this.get('comment').length > 0;
    }.property('comment'),

    actions: {
        delete: function() {
            var update = this.get('model');
            var parent = update.get('item.updates');
            if (confirm('정말로 삭제하시겠습니까?')) {
                update.deleteRecord().then(function() {
                    // XXX: expensive
                    update.get('item').reload();
                });
            }
        }
    }
});

App.RadioButton = Ember.View.extend({
    tagName: 'input',
    type: 'radio',
    attributeBindings: ['name', 'type', 'value', 'checked:checked:'],
    click: function() {
        this.set('selection', this.$().val());
    },
    checked: function() {
        return this.get('value') == this.get('selection')
    }.property('selection')
});

App.AutoSelectTextField = Ember.TextField.extend({
    focusIn: function() {
        this.$().select();
    }
});

App.CheckableDropdownItem = Ember.View.extend({
    classNameBindings: [':dropdown-item', 'selected'],
    template: Ember.Handlebars.compile('{{view.title}} {{#if view.selected}}<i class="icon-ok"></i>{{/if}}'),
    click: function() {
        this.set('selection', this.get('value'));
    },
    selected: function() {
        return this.get('selection') == this.get('value');
    }.property('selection')
});

App.DropdownButton = Ember.View.extend({
    open: false,
    classNameBindings: [':dropdown-container', 'open'],
    layout: Ember.Handlebars.compile('{{#view view.button titleBinding="view.title"}}<i class="icon-gear"></i> {{view.title}} <i class="caret icon-caret-down"></i>{{/view}}{{#view view.dropdown}}{{yield}}{{/view}}'),
    button: Ember.View.extend({
        tagName: 'span',
        classNames: ['btn-dropdown'],
        mouseEnter: function() {
            var parent = this.get('parentView');
            if (parent)
                parent.set('open', true);
        },
        mouseLeave: function() {
            var parent = this.get('parentView');
            if (parent)
                parent.set('open', false);
        }
    }),
    dropdown: Ember.View.extend({
        tagName: 'div',
        classNames: ['dropdown'],
        mouseEnter: function() {
            var parent = this.get('parentView');
            if (parent)
                parent.set('open', true);
        },
        mouseLeave: function() {
            var parent = this.get('parentView');
            if (parent)
                parent.set('open', false);
        },
        click: function() {
            var parent = this.get('parentView');
            if (parent)
                parent.set('open', false);
        }
    }),
});
