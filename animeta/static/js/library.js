var App = Ember.Application.create({
    rootElement: '#app-root',
    LOG_TRANSITIONS: true
});

App.Router.map(function() {
    this.resource('library', {path: '/'}, function() {
        this.route('item', {path: '/items/:item_id'});
    });
});

App.LibraryItem = Ember.Object.extend({
    saveStatus: function() {
        return Ember.$.post('/items/' + this.get('id'), {status: this.get('status')});
    }
});

App.Update = Ember.Object.extend({
    progressSuffix: function() {
        return this.get('progress').match(/(^$)|([0-9]$)/) ? '화' : '';
    }.property('progress'),

    save: function() {
        var data = {
            progress: this.get('progress'),
            comment: this.get('comment')
        };
        var self = this;
        return Ember.$.post('/items/' + this.get('item.id') + '/updates', data).then(function(d) {
            // TODO: update item properties
            d.updatedAt = new Date(d.updatedAt * 1000);
            d.item = self.get('item');
            return App.Update.create(d);
        });
    }
});

App.LibraryRoute = Ember.Route.extend({
    model: function() {
        return App.DATA_ITEMS;
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
    }.property('@each.updatedAt')
});

App.STATUS_TEXTS = {
    watching: '보는 중',
    finished: '완료',
    suspended: '중단',
    intersted: '관심'
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
        return App.DATA_ITEMS.find(function(item) {
            return item.get('id') == params.item_id;
        });
    },

    setupController: function(controller, model) {
        controller.set('model', model);
        Ember.$.getJSON('/items/' + model.get('id') + '/updates').then(function(data) {
            model.set('updates', data.map(function(data) {
                data.updatedAt = new Date(data.updatedAt * 1000);
                data.item = model;
                return App.Update.create(data);
            }));
        });
    },

    actions: {
        close: function() {
            this.transitionTo('library');
        }
    }
});

App.LibraryItemController = Ember.ObjectController.extend({
    canEdit: function() {
        return this.get('userId') == App.CURRENT_USER_ID;
    }.property('userId'),

    newUpdate: function() {
        return App.Update.create({
            item: this.get('model'),
            progress: this.get('progress')
        });
    }.property('model'),

    statusChanged: function() {
        this.get('model').saveStatus();
    }.observes('status'),

    actions: {
        saveUpdate: function() {
            var self = this;
            var newUpdate = this.get('newUpdate');
            newUpdate.save().then(function(update) {
                self.get('updates').unshiftObject(update);
                newUpdate.set('comment', '');
            });
        }
    }
});

App.UpdateController = Ember.ObjectController.extend({
    needs: 'libraryItem',

    progressText: function() {
        return this.get('progress') + this.get('progressSuffix');
    }.property('progress', 'progressSuffix'),

    updatedAtFromNow: function() {
        return moment(this.get('updatedAt')).fromNow();
    }.property('updatedAt'),

    canEdit: Ember.computed.alias('controllers.libraryItem.canEdit'),

    actions: {
        delete: function() {
            var self = this;
            if (confirm('정말로 삭제하시겠습니까?')) {
                Ember.$.ajax('/updates/' + this.get('id'), {type: 'DELETE'}).then(function() {
                    self.get('item.updates').removeObject(self.get('model'));
                    // TODO: update item progress
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
