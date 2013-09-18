var App = Ember.Application.create({
    rootElement: '#app-root',
    LOG_TRANSITIONS: true
});

App.Router.map(function() {
    this.resource('library', {path: '/'}, function() {
        this.route('item', {path: '/items/:item_id'});
    });
});

App.LibraryItem = Ember.Object.extend({});

App.LibraryRoute = Ember.Route.extend({
    model: function() {
        return App.DATA_ITEMS;
    }
});

App.LibraryItemRoute = Ember.Route.extend({
    model: function(params) {
        return App.DATA_ITEMS.find(function(item) {
            return item.get('id') == params.item_id;
        });
    },
    actions: {
        close: function() {
            this.transitionTo('library');
        }
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
    sortProperties: ['updated_at'],
    sortAscending: false,
    sectionedContents: function() {
        var sections = [], section = null;
        this.forEach(function(item) {
            var h = getDateHeader(item.get('updated_at'));
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
    }.property('@each.updated_at')
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
