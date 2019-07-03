/*
	2017.11
*/

!function($){
	var xSelect = function(element,options){
		if (options['module_type'] == undefined){
			this._id = (((1 + Math.random()) * 0x10000) | 0).toString(16);
		}else{
			this._id = options['module_type'];
		}
		//this._id = (((1 + Math.random()) * 0x10000) | 0).toString(16);
		this.opts = options;
		this._initLayout($(element));
	};

	xSelect.prototype = {
		_initLayout: function($el){
			var opts = this.opts;

			var xSelect = [
				'<div class="xSelect-show" data-id="xSelect-'+this._id+'">',
					'<span class="xSelect-show-text"></span>',
				'</div>'
			];

			var xSelectView = [
				'<div class="xSelect-view xSelect-'+this._id+'" data-id="xSelect-'+this._id+'">',
					'<input class="xSelect-select-filter" type="text" name="" />',
					'<ul />',
					'<div class="xSelect-select-btn"></div>',
				'</div>'
			]

			var $xSelect = $(xSelect.join('')),
				$xSelectView = $(xSelectView.join(''));

			this.$xSelect = $xSelect;
			this.$xSelectView = $xSelectView;

			this.$text = $xSelect.find('span.xSelect-show-text');

			this.$filter = $xSelectView.children('input.xSelect-select-filter');
			this.$list = $xSelectView.children('ul');
			this.$btn = $xSelectView.children('div.xSelect-select-btn');

			this._initContainer();

			this._initView();
			$el.empty().html($xSelect);

			if(opts.disable){
				$xSelect.addClass('xSelect-disable');
			}else{
				this._initEvent();
				//$('body').append($xSelectView);
				//var $_cc = $('body').find('.c-cont');

				//if($_cc.length > 0){
				//	$_cc.eq(0).append($xSelectView);
				//}else{
					$('body').append($xSelectView);
				//}
				
			}

			if(!opts.filter){
				this.$filter.remove();
			}

			if(!opts.btn){
				this.$btn.remove();
				opts.num = 1;
			}else{
                opts.num = 2;
            }
		},

		_initContainer: function(){
			var that = this;
			var opts = this.opts;
			var $text = this.$text;

			$text.html(opts.defaultText).parent().css('width',opts.width);
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
				for(i in opts.items){
					var item=opts.items[i];
					if(item.flag_pwd !=undefined)
						var $li = $('<li><span flag_pwd="'+item.flag_pwd+'" usbkeylen="'+item.usbkeylen+'" data-value="'+item.value+'" style="" title="'+item.name+'">'+item.name+'</span></li>');
					else if(item.access_flag !=undefined){
						var $li = $('<li><span access_flag="'+item.access_flag+'" pwd_flag="'+item.pwd_flag+'" data-value="'+item.value+'" style="" title="'+item.name+'">'+item.name+'</span></li>');
					}else
						var $li = $('<li><span data-value="'+item.value+'" style="" title="'+item.name+'">'+item.name+'</span></li>');
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

		_setPosition: function(i){
			var that = this;
			var opts = this.opts;
			var $xSelect = this.$xSelect;
			var $xSelectView = this.$xSelectView;
			var $filter = this.$filter;

			var _fixPos = 0;

			var $_cc = $xSelect.parents('.c-cont');
			var $_dd = $xSelect.parents('.ui-popup');

			var offset = $xSelect.offset();
			var bh = document.documentElement.clientHeight || document.body.clientHeight;
			var st = document.documentElement.scrollTop || document.body.scrollTop;
			var st2 = 0;
			//var sh = $xSelectView.outerHeight();

			var sh = 0;
			var xlen = $xSelectView.find('li:visible').length;
			if(xlen>=5){
				sh = 220 - (2 - opts.num) * 30;
			}else{
				sh = (xlen + opts.num) * 30 + 10;
			}

			$(document).unbind('scroll');

			$('div.c-cont').unbind('scroll');

			/*
			if($_cc.length > 0){
				_fixPos = 37;

				bh = $('.c-cont:first').height();
				st2 = $('.c-cont:first').scrollTop();
			}

			if($_dd.length > 0){
				var clen = $('.c-cont:visible').length;
				var dlen = $_dd.find('.c-cont').length;
				if(clen != dlen){
					_fixPos = 37;
					bh = $('.c-cont:first').height();
					st2 = $('.c-cont:first').scrollTop();
				}else{
					_fixPos = 0;
					$xSelectView.appendTo('body');
				}
			}
			*/

			var check = true;

			//if($('body').find('div.c-cont').length == 1){
			//	check = offset.top + sh <= bh;
			//}else{
				check = offset.top + $xSelect.height() + 1 + sh <= st + bh + st2;
			//}

			if(i == 1){
				//if(offset.top + $xSelect.height() + 1 + sh <= st + bh + st2){
				if(check){
					$xSelect.addClass('on-above').removeClass('on-bellow');
					$xSelectView.addClass('on-above').removeClass('on-bellow').css({
						top: offset.top + $xSelect.height() + 1 - _fixPos + st2,
						left: offset.left
					});

					$filter.prependTo($xSelectView).focus();
				}else{
					$xSelect.addClass('on-bellow').removeClass('on-above');
					$xSelectView.addClass('on-bellow').removeClass('on-above').css({
						top: offset.top - sh + 1 - _fixPos + st2,
						left: offset.left
					});

					$filter.appendTo($xSelectView).focus();

					if($xSelectView.offset().top < 40){
						$xSelect.addClass('on-above').removeClass('on-bellow');
						$xSelectView.addClass('on-above').removeClass('on-bellow').css({
							top: offset.top + $xSelect.height() + 1 - _fixPos + st2,
							left: offset.left
						});

						$filter.prependTo($xSelectView).focus();
					}
				}
			}else{
				var  c = $xSelect.attr('class').split(' ');

				if($.inArray('on-above',c) >=0 ){
					$xSelectView.css({
						top: offset.top + $xSelect.height() + 1 - _fixPos + st2,
						left: offset.left
					});
				}else{
					$xSelectView.css({
						top: offset.top - sh + 1 - _fixPos + st2,
						left: offset.left
					});
				}
			}

			var sleft = $xSelect.offset().left,
				vleft = $xSelectView.offset().left;

			if(sleft != vleft){
				$xSelectView.css('left',sleft);
			}
			
			$(document).on('scroll',function(e){
				$xSelect.attr('class','xSelect-show');
				$xSelectView.hide();
			});

			$('div.c-cont').on('scroll',function(e){
				$xSelect.attr('class','xSelect-show');
				$xSelectView.hide();
			});
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
				$filter.val('');
				$list.children('li').show();

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
					if((xv || xv==0) && v == xv){
						$(this).parent().addClass('active').siblings().removeClass('active');

						var index = $(this).parent().index() - 1;

						$list.scrollTop(30*index);
					}
				});

				//$list.unbind('mousewheel');

				$(document).on('mousewheel',function(e){
					e.preventDefault();
          			e.stopPropagation();
				});
			}

			var _hide;
			var _hideView = function(){
				//_hide = setTimeout(function(){
					$xSelect.removeClass('on');
					$xSelectView.hide();

					$(document).unbind('mousewheel');
				//},20);
			}

			var scroll = function(event,scroller){
			    var k = event.wheelDelta? event.wheelDelta:-event.detail*10;
			    scroller.scrollTop = scroller.scrollTop - k;
			    return false;
			};

			$xSelect.on('click',function(){
				var xclass = $xSelect.attr('class').split(' ');
				if($.inArray('xSelect-disable',xclass)>=0){
					return false;
				}
				if($.inArray('on',xclass) < 0){
					$xSelect.addClass('on');
					_getView();
					$(document).on('click',function(){
						clearTimeout(_hide);
					});
				}else{
					$xSelect.removeClass('on');
					$(document).on('click',function(){
						//_hideView();
					});

					_hideView();
				}
			});

			$xSelectView.hover(function(){
				$(document).on('click',function(){
					clearTimeout(_hide);
				});
			},function(){
				$(document).on('click',function(){
					//_hideView();
				});
			});

			$(document).on('click',function(e){
				var $_o = $(e.target);

				var //$_p1 = $('div.xSelect-view'),
					$_p2 = $_o.parents('div.xSelect-view'),
					//$_p3 = $('div.xSelect-show'),
					$_p4 = $_o.parents('div.xSelect-show');

				
				if($_p2.length == 0 && $_p4.length == 0){
					_hideView();
				}
				
			});

			$list.on('click','span',function(){
				var text = $(this).text();
				var value = $(this).data('value');

				$('span',$xSelect).text(text);
				$xSelect.parent().data('value',value);
				if(opts['setval'] && typeof opts['setval'] == 'function'){
					opts['setval'](opts.items[value],$(this).parent());
				}
				$(document).on('click',function(){
					//_hideView();
				});
				_hideView();
			}).on('click','i',function(){
				var i = $(this).next().data("value");
				var iclass = $(this).attr('class');

				if(opts[iclass] && typeof opts[iclass] == 'function'){
					opts[iclass](opts.items[i],$(this).parent());
				}
			});

			$list.parent().on('click','a.xSelect-select-btn',function(){
				_hideView();
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

				$(document).on('click',function(){
					//_hideView();
				});
			});

			$(window).on('resize',function(){
				_hideView();
			});

			/*
			$(document).on('scroll',function(e){
				_hideView();
			});

			$('div.c-cont').on('scroll',function(e){
				_hideView();
			});
			*/

			$list.on('mousewheel',function(e){
				var s = e.deltaY;
				var t = $list.scrollTop();
				if( s == -1 ){
					t += 15;
				}else if( s == 1 ){
					t -= 15;
				}

				$list.scrollTop(t);
			})
		},

		_hide: function(){
			var $xSelect = this.$xSelect;
			var $xSelectView = this.$xSelectView;

			$xSelect.removeClass('on');
			$xSelectView.hide();
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
        , disable: false
    };

    $.fn.xSelect.Constructor = xSelect;
}(window.jQuery);



!function(a){"function"==typeof define&&define.amd?define(["jquery"],a):"object"==typeof exports?module.exports=a:a(jQuery)}(function(a){function b(b){var g=b||window.event,h=i.call(arguments,1),j=0,l=0,m=0,n=0,o=0,p=0;if(b=a.event.fix(g),b.type="mousewheel","detail"in g&&(m=-1*g.detail),"wheelDelta"in g&&(m=g.wheelDelta),"wheelDeltaY"in g&&(m=g.wheelDeltaY),"wheelDeltaX"in g&&(l=-1*g.wheelDeltaX),"axis"in g&&g.axis===g.HORIZONTAL_AXIS&&(l=-1*m,m=0),j=0===m?l:m,"deltaY"in g&&(m=-1*g.deltaY,j=m),"deltaX"in g&&(l=g.deltaX,0===m&&(j=-1*l)),0!==m||0!==l){if(1===g.deltaMode){var q=a.data(this,"mousewheel-line-height");j*=q,m*=q,l*=q}else if(2===g.deltaMode){var r=a.data(this,"mousewheel-page-height");j*=r,m*=r,l*=r}if(n=Math.max(Math.abs(m),Math.abs(l)),(!f||f>n)&&(f=n,d(g,n)&&(f/=40)),d(g,n)&&(j/=40,l/=40,m/=40),j=Math[j>=1?"floor":"ceil"](j/f),l=Math[l>=1?"floor":"ceil"](l/f),m=Math[m>=1?"floor":"ceil"](m/f),k.settings.normalizeOffset&&this.getBoundingClientRect){var s=this.getBoundingClientRect();o=b.clientX-s.left,p=b.clientY-s.top}return b.deltaX=l,b.deltaY=m,b.deltaFactor=f,b.offsetX=o,b.offsetY=p,b.deltaMode=0,h.unshift(b,j,l,m),e&&clearTimeout(e),e=setTimeout(c,200),(a.event.dispatch||a.event.handle).apply(this,h)}}function c(){f=null}function d(a,b){return k.settings.adjustOldDeltas&&"mousewheel"===a.type&&b%120===0}var e,f,g=["wheel","mousewheel","DOMMouseScroll","MozMousePixelScroll"],h="onwheel"in document||document.documentMode>=9?["wheel"]:["mousewheel","DomMouseScroll","MozMousePixelScroll"],i=Array.prototype.slice;if(a.event.fixHooks)for(var j=g.length;j;)a.event.fixHooks[g[--j]]=a.event.mouseHooks;var k=a.event.special.mousewheel={version:"3.1.12",setup:function(){if(this.addEventListener)for(var c=h.length;c;)this.addEventListener(h[--c],b,!1);else this.onmousewheel=b;a.data(this,"mousewheel-line-height",k.getLineHeight(this)),a.data(this,"mousewheel-page-height",k.getPageHeight(this))},teardown:function(){if(this.removeEventListener)for(var c=h.length;c;)this.removeEventListener(h[--c],b,!1);else this.onmousewheel=null;a.removeData(this,"mousewheel-line-height"),a.removeData(this,"mousewheel-page-height")},getLineHeight:function(b){var c=a(b),d=c["offsetParent"in a.fn?"offsetParent":"parent"]();return d.length||(d=a("body")),parseInt(d.css("fontSize"),10)||parseInt(c.css("fontSize"),10)||16},getPageHeight:function(b){return a(b).height()},settings:{adjustOldDeltas:!0,normalizeOffset:!0}};a.fn.extend({mousewheel:function(a){return a?this.bind("mousewheel",a):this.trigger("mousewheel")},unmousewheel:function(a){return this.unbind("mousewheel",a)}})});
