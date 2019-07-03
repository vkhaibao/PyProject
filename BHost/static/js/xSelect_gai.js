/*
	2017.11
*/

!function($){
	var xSelect = function(element,options){
		this._id = (((1 + Math.random()) * 0x10000) | 0).toString(16);
		this.opts = options;
		this._initLayout($(element));
	};

	xSelect.prototype = {
		_initLayout: function($el){
			var opts = this.opts;

			var xSelect = [
				'<div class="xSelect-show" data-id="xSelect-'+this._id+'">',
					'<input class="xSelect-show-text" readonly>',
				'</div>'
			];

			var xSelectView = [
				'<div class="xSelect-view" data-id="xSelect-'+this._id+'">',
					'<input class="xSelect-select-filter" type="text" name="" />',
					'<ul />',
					'<div class="xSelect-select-btn"></div>',
				'</div>'
			]

			var $xSelect = $(xSelect.join('')),
				$xSelectView = $(xSelectView.join(''));

			this.$xSelect = $xSelect;
			this.$xSelectView = $xSelectView;

			this.$text = $xSelect.find('input.xSelect-show-text');

			this.$filter = $xSelectView.children('input.xSelect-select-filter');
			this.$list = $xSelectView.children('ul');
			this.$btn = $xSelectView.children('div.xSelect-select-btn');

			this._initContainer();
			this._initView();
			this._initEvent();
			$el.empty().html($xSelect);

			$('body').append($xSelectView);

			if(!opts.filter){
				this.$filter.remove();
			}

			if(!opts.btn){
				this.$btn.remove();
			}
		},

		_initContainer: function(){
			var that = this;
			var opts = this.opts;
			var $text = this.$text;

			$text.val(opts.defaultText).parent().css('width',opts.width);
		},

		_initView: function(i){
			var that = this;
			var opts = this.opts;
			var $xSelectView = this.$xSelectView;
			var $filter = this.$filter;
			var $list = this.$list;
			var $btn = this.$btn;

			$xSelectView.css('width',opts.width);
			var aw = parseInt(opts.width) - 30;
			if(typeof opts.items == 'object'){
				/*
				$.each(opts.items,function(i,item){
					var $li = $('<li><span data-value="'+item.value+'" style="width:'+aw+'px">'+item.name+'</span></li>');
					if(item.type){
						$li.prepend('<i class="'+item.type+'" />');
					}

					$list.append($li);
				})
				*/
				for(i in opts.items){
					var item=opts.items[i];
					var $li = $('<li><span data-value="'+item.value+'" style="width:'+aw+'px">'+item.name+'</span></li>');
                                        if(item.type){
                                                $li.prepend('<i class="'+item.type+'" />');
                                        }

                                        $list.append($li);
				}
			}else{
				alert('数据错误');
			}

			if(opts.btn && typeof opts.btn == 'object' ){
				$.each(opts.btn,function(i,item){
					$btn.append('<a class="xSelect-select-btn" href="javascript:;">'+item.name+'</a>');
				});
			}
		},

		_initData: function(){
			
		},

		_setPosition(i){
			var that = this;
			var opts = this.opts;
			var $xSelect = this.$xSelect;
			var $xSelectView = this.$xSelectView;
			var $filter = this.$filter;

			var offset = $xSelect.offset();
			var bh = document.documentElement.clientHeight || document.body.clientHeight;
			var st = document.documentElement.scrollTop || document.body.scrollTop;
			var sh = $xSelectView.outerHeight();

			if(i == 1){
				if(offset.top + $xSelect.height() + 1 + sh <= st + bh){
					$xSelect.addClass('on-above');
					$xSelectView.addClass('on-above').css({
						top: offset.top + $xSelect.height() + 1,
						left: offset.left
					});

					$filter.prependTo($xSelectView).focus();
				}else{
					$xSelect.addClass('on-bellow');
					$xSelectView.addClass('on-bellow').css({
						top: offset.top - sh + 1,
						left: offset.left
					});

					$filter.appendTo($xSelectView).focus();
				}
			}else{
				var  c = $xSelect.attr('class').split(' ');

				if($.inArray('on-above',c) >=0 ){
					$xSelectView.css({
						top: offset.top + $xSelect.height() + 1,
						left: offset.left
					});
				}else{
					$xSelectView.css({
						top: offset.top - sh + 1,
						left: offset.left
					});
				}
			}
			
		},

		_initEvent: function(){
			var that = this;
			var opts = this.opts;
			var $xSelect = this.$xSelect;
			var $xSelectView = this.$xSelectView;

			var $list = this.$list;
			var $filter = this.$filter;
			var $btn = this.$btn;

			var _getView = function(){
				$('.xSelect-show').removeClass('on');
				$('.xSelect-view').hide();
				$xSelect.addClass('on');
				$xSelectView.show();
				$('.xSelect-select-filter',$xSelectView).val('');
				$('li',$xSelectView).show();
				that._setPosition(1);

				var xv = $xSelect.parent().data('value');

				$('li>span',$list).each(function(i,item){
					var v = $(this).data('value');

					if(xv && v == xv){
						$(this).parent().addClass('active').siblings().removeClass('active');
					}
				})
			}

			var _hide;
			var _hideView = function(){
				_hide = setTimeout(function(){
					$xSelect.attr('class','xSelect-show');
					$xSelectView.hide();
				},20);
			}

			$xSelect.on('click',function(){
				var xclass = $xSelect.attr('class').split(' ');
				if($.inArray('on',xclass) < 0){
					$xSelect.addClass('on');
					_getView();
					document.onclick = function(){
						clearTimeout(_hide);
					}
				}else{
					$xSelect.removeClass('on');
					document.onclick = function(){
						_hideView();
					}
				}
			});

			$xSelectView.hover(function(){
				document.onclick = function(){
					clearTimeout(_hide);
				}
			},function(){
				document.onclick = function(){
					_hideView();
				}
			});

			$list.on('click','span',function(){
				var text = $(this).text();
				var value = $(this).data('value');

				$('input',$xSelect).val(text);
				$xSelect.parent().data('value',value);
				document.onclick = function(){
					_hideView();
				}
			}).on('click','i',function(){
				var i = $(this).next('span').data("value");
				var iclass = $(this).attr('class');

				if(opts[iclass] && typeof opts[iclass] == 'function'){
					opts[iclass](opts.items[i],$(this).parent());
				}
			});

			$filter.on('keyup',function(){
				var v = $(this).val().trim();
				if(v == ''){
					$('li',$list).show();
				}else{
					$('li',$list).each(function(){
						var txt = $(this).text();
						if(txt.indexOf(v) >= 0){
							$(this).show();
						}else{
							$(this).hide();
						}
					})
				}

				that._setPosition();
			});

			$btn.on('click','a',function(){
				var i = $(this).index();

				if(opts.btn[i].event && typeof opts.btn[i].event == 'function'){
					opts.btn[i].event(opts.items,$(this));
				}

				document.onclick = function(){
					_hideView();
				}
			});

			$(window).on('scroll',function(){
				_hideView();
			})
		}
	};

	$.fn.xSelect = function(){
        if(arguments.length === 0 || typeof arguments[0] === 'object'){
            var option = arguments[0]
                , data = this.data('xSelect')
                , options = $.extend(true, {}, $.fn.xSelect.defaults, option);
            if (!data) {
                data = new xSelect(this, options);
                this.data('xSelect', data);
            }
            return $.extend(true, this, data);
        }
        if(typeof arguments[0] === 'string'){
            var data = this.data('xSelect');
            var fn =  data[arguments[0]];
            if(fn){
                var args = Array.prototype.slice.call(arguments);
                return fn.apply(data,args.slice(1));
            }
        }
    };

    $.fn.xSelect.defaults = {
        width: 120
        , items: []
        , url: false
        , data: {}
        , method: 'POST'
        , cache: false
        , edit: null
        , delect: null
        , btn: null
        , defaultText: '请选择'
        , defaultValue: null
        , filter: true
    };

    $.fn.xSelect.Constructor = xSelect;
}(window.jQuery);
