/* 
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

define('providers/edit', [
    'providers',
	'utils/str',
	'jquery',
	'gizmo/superdesk',	
	config.guiJs('livedesk', 'models/posttype'),
	config.guiJs('livedesk', 'models/post'),
    'jquery/utils',
    'jquery/rest',
    'jquery/superdesk',
    'jquery/tmpl',
    'jquery/avatar',
	'jqueryui/draggable',
    'jqueryui/texteditor',
    'tmpl!livedesk>providers/edit',
    'tmpl!livedesk>providers/edit/item',
], function( providers, str, $, Gizmo ) {
	$.extend(providers.edit, {
		init: function(theBlog) {
			var OwnCollection = Gizmo.AuthCollection.extend({
				insertFrom: function(model) {
					this.desynced = false;
					if( !(model instanceof Gizmo.AuthModel) ) model = new this.model(model);
					this._list.push(model);
					model.hash();
					var x = model.sync(model.url.root(theBlog).xfilter('Id,AuthorName,Content,Type.Key,PublishedOn,CreatedOn,Author.Source.Name'));
					return x;			
				}
			}),
			ownCollection = new OwnCollection(
				theBlog+ '/Post/Owned?X-Filter=Id,AuthorName,Content,Type.Key,PublishedOn,CreatedOn,Author.Source.Name',
				Gizmo.Register.Post
			);
			//ownCollection.xfilter('Id,AuthorName,Content,Type.Key,PublishedOn,CreatedOn,Author.Source.Name');
			
			var postTypeCollection = new Gizmo.AuthCollection('http://localhost:8082/resources/Superdesk/PostType', Gizmo.Register.PostType);
			postTypeCollection.xfilter('Key');
		
			var PostView = Gizmo.View.extend({		
				events: { 
					"": { "dragstart": "adaptor"}
				},
				render: function(){
					var avatar = $.avatar.get($.superdesk.login.EMail);
					var self = this;
					if(!(this.model instanceof Gizmo.Register.Post))
						this.model = new Gizmo.Register.Post(this.model);
					$.tmpl('livedesk>providers/edit/item', { Post: this.model.feed(),Avatar: avatar} , function(err, out){
						self.el = $(out);
						if(!self.model.get('PublishedOn')) {
									self.el.draggable({
										revert: 'invalid',
										containment:'document',
										helper: 'clone',
										appendTo: 'body',
										zIndex: 2700
									});
						}
						self.resetEvents();
					});
					return this;
				},
				adaptor: function(evt){
					$(evt.target).parents('li').data("post", this.model.get('Id'));
				}
			});
			var PostsView = Gizmo.View.extend({
				init: function(){
					var self = this;
					this.posts = ownCollection;
					this.posts.on('read', function(){
						self.render();
					});
					this.posts.model.on('insert', function(evt, model){
						self.addOne(model);
					});
					this.posts.sync();
				},
				render: function(){
					var self = this;
					this.posts.each(function(key, model){
						self.addOne(model, true);
					});
				},
				insert: function(model)
				{
					var self = this;
					this.posts.insertFrom(model);
				},
				addOne: function(model, order)
				{
					var view = new PostView({model: model, _parent: this}, { events: false, ensure: false});				
					if(order)
						this.el.append(view.render().el);
					else
						this.el.prepend(view.render().el);
				}
			}); 
			var EditView = Gizmo.View.extend({
				postView: null,
				events: {
					'[ci="savepost"]': { 'click': 'savepost'},
					'[ci="save"]': { 'click': 'save'}
				},
				init: function(){
					this.postTypes = postTypeCollection;
					this.postTypes.on('read', this.render, this);
					this.postTypes.sync();
				},
				render: function(){
					var self = this;
					this.el.tmpl('livedesk>providers/edit', { PostTypes: this.postTypes.feed() }, function(){
						// editor 
						fixedToolbar = 
						{
							_create: function(elements)
							{
								var self = this;
								$(elements).on('toolbar-created', function()
								{
									self.plugins.toolbar.element.hide()
										.appendTo($('.edit-block .toolbar-placeholder')); 
								}); 
								$(elements).on('focusin.texteditor keydown.texteditor click.texteditor', function(event)
								{
									self.plugins.toolbar.element.fadeIn('fast');
								});
								$(elements).on('blur.texteditor focusout.texteditor', function()
								{ 
									self.plugins.toolbar.element.fadeOut('fast'); 
								});
							}
						};
						self.el.find('.edit-block article.editable').texteditor({ plugins: 
						{
							floatingToolbar: null, 
							draggableToolbar: null, 
							fixedToolbar: fixedToolbar
						}});
						self.postsView = new PostsView({ el: $(this).find('#own-posts-results'), _parent: self});
					} );
				},
				savepost: function(evt){
					evt.preventDefault();
					var data = {
						Content: $.styledNodeHtml(this.el.find('.edit-block article.editable')),
						Type: this.el.find('[name="type"]').val()
					};
					this.postsView.insert(data);
				},
				save: function(evt){
					evt.preventDefault();
					
				}
			});
			new EditView({ el: this.el});
		}
	});
	return providers;	
});