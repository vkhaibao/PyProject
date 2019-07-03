/*
	2017.11
*/

!function($){
	var _global_left=0;
	var xTable = function(element,options){
		this._id = (((1 + Math.random()) * 0x10000) | 0).toString(16);
		this.opts = options;
		this._initLayout($(element));
		//this._initSel();
		//this._initHead();
		//this._initBody();
	};

	xTable.prototype = {
		_initLayout: function($el){
			var opts = this.opts;
			if(navigator.userAgent.indexOf("Chrome") >-1){
				var hei = 440;
			}else{
				var hei = 447;
			}
			
			var xTable = [
				'<div class="xTable">',
					'<div class="xTable-head">',
						'<div class="xTable-head-w">',
							'<span class="xTable-head-btn">列表展示项</span>',
							'<ul />',
						'</div>',
					'</div>',
					'<div class="xTable-body-wrapper" style="border: 1px solid rgb(221,221,221);">',
						'<div class="xTable-body" id="theadDiv_xTable" style="height: 40px;overflow: hidden;">',
							'<table cellspacing="0" cellpadding="0" border="0">',
									'<thead />',
							'</table>',
						'</div>',
						'<div class="xTable-body" id="tbodyDiv_xTable" style="height: '+hei+'px;overflow-y:auto">',
							'<table cellspacing="0" cellpadding="0" border="0">',
								'<tbody />',
							'</table>',
						'</div>',
					'</div>',
					'<div class="xTable-page"></div>',
				'</div>'
			];

			var $xTable = $(xTable.join(''));
			this.$xTable = $xTable;
			this.$sel = $xTable.children('div.xTable-head');
			this.$head = $xTable.find('div.xTable-body').children('table').children('thead');
			this.$body = $xTable.find('div.xTable-body').children('table').children('tbody');
			this.$page = $xTable.children('div.xTable-page');

			if(opts.select){
				this._initSel();
			}else{
				this.$sel.remove();
			}

			if(!opts.showPage){
				this.$page.remove();
			}
			
			
			this._initHead();
			this._initBody();
			this._initEvent();
			$el.empty().html($xTable);
			
			$('#tbodyDiv_xTable').on('scroll', function () {
	            $("#theadDiv_xTable").scrollLeft($('#tbodyDiv_xTable').scrollLeft());
				//alert(this._global_left);
       		});
		},

		_initSel: function(){
			var opts = this.opts;
			var $sel = this.$sel;
			var cols = opts.cols;

			if(opts.select){
				var $_list = $sel.find('ul');
				$_list.empty();
				$.each(cols,function(i,item){
					if(item.infoDiv){
						return;
					}

					if(item.hide){
						$_list.append('<li data-index="'+i+'"><label><input type="checkbox" value="'+item.name+'" _id="'+item.field_id+'" /><span class="check"></span></label><span class="sortBtn">'+item.title+'</span></li>');
					}else if(item.lock){
						$_list.append('<li data-index="'+i+'"><label><input type="checkbox" checked disabled="true" value="'+item.name+'" _id="'+item.field_id+'" /><span class="check"></span></label><span class="sortBtn">'+item.title+'</span></li>');
					}else{
						$_list.append('<li data-index="'+i+'"><label><input type="checkbox" checked value="'+item.name+'" _id="'+item.field_id+'" /><span class="check"></span></label><span class="sortBtn">'+item.title+'</span></li>');
					}
				});
			}
			
		},

		_initHead: function(){
			var that = this;
			var opts = this.opts;
			var $sel = this.$sel;
			var cols = opts.cols;
			var showWidth = 0;
			var setWidth = true;

			var $head = this.$head;
			$head.empty();
			var $_tr = $('<tr />');

			$.each(cols,function(i,item){
				var align = item.align;
				var width = item.width;
				var name = item.name;
				var title = item.title;
				var hide = false;

				if(item.infoDiv){
					return;
				}

				if(typeof item.hide != 'undefined'){
					hide = item.hide;
				}

				if(typeof width == 'number'){
					width += 'px';
				}

				if(width.indexOf('%') > 0){
					setWidth = false;
				}

				if(!hide){
					$_tr.append('<th style="text-align:'+align+'" width="'+width+'" data-role="'+name+'">'+title+'</th>');

					var wn = parseInt(width);
					showWidth += wn;
				}else{
					//$_tr.append('<th style="text-align:'+align+';display:none;" width="'+width+'" data-role="'+name+'" title="'+title+'">'+title+'</th>');
				}
			});

			$head.html($_tr);
		},

		_initBody: function(i){			
			_global_left = $('#tbodyDiv_xTable').scrollLeft();
			//alert(_global_left);
			var that = this;
			var opts = this.opts;
			var $body = this.$body;
			var $page = this.$page;
			var cols = opts.cols;
			var btns = opts.btns;
			var btnShow = false;
			var btnHtml;
			this.mname = '';

			$body.empty();
			
			this.btnShow = btnShow;
			var page = opts.data.page;
			var limit = opts.data.limit;

			var dp = $page.data('page');
			var dl = $page.data('limit');

			if(!page){
				page = 1;
			}

			if(!limit){
				limit = 10;
			}
			if(limit>500){
				limit = 500;
			}
			opts.data.page = page;
			opts.data.limit = limit;

			if(dp){
				opts.data.page = dp;
			}

			if(dl){
				opts.data.limit = dl;
			}

			if(i && i == 'native'){
				that._initData(_xTable_Data.items,btnShow);
				return;
			}
			
			if(navigator.userAgent.indexOf("Chrome") >-1){
				$body.parents('div.xTable-body-wrapper').css({
					'height': 43 * (Number(MAX_PAGE ) + 1) +7
					, 'overflow': 'auto'
				});
			}else{
				$body.parents('div.xTable-body-wrapper').css({
					'height': 44 * (Number(MAX_PAGE ) + 1) +5
					, 'overflow': 'auto'
				});
				
			}

			$.ajax({
				url: opts.url,
				type: opts.method,
				data: opts.data,
				dataType: 'json',
				cache: false,
			}).done(function(result){
				var data = result;
				var items = data.items;

				that.opts.items = items;
				if(result.items.length && result.items.length != 0){
					_xTable_Data = result;
				}else{
					_xTable_Data = []	
				}

				that._initData(opts.items,btnShow);

				that._initPage(result);

				if(opts.success && typeof opts.success == 'function'){
					opts.success(data);
				}

				if(opts.dblclick && typeof opts.dblclick == 'function'){
					$body.on('dblclick','tr',function(){
						var i = $(this).index();
						opts.dblclick(_xTable_Data.items[i],_xTable_Data.items);
					})
				}
				if(typeof(from_flag) != 'undefined'){
                                        if(from_flag == 'search')$('#tbodyDiv_xTable').height($('body').height()-258 + 36);
                                        else $('#tbodyDiv_xTable').height($('body').height()-258);
                                 }else{
                                         $('#tbodyDiv_xTable').height($('body').height()-258);
                                 }

                                $('.xTable-body-wrapper').height($('#tbodyDiv_xTable').height() + 40)
			})
		},

		_initData: function(data,btnShow){
			var that = this;
			var opts = this.opts;
			var $body = this.$body;
			var btns = opts.btns;
			var btnHtml;
			//
			var $sel = this.$sel;

			$('input:checkbox',$sel).each(function(i,item){
				var val = $(item).val();
				var check = $(item).prop('checked');

				var hide;

				if(check){
					hide = false;
				}else{
					hide = true;
				}

				$.each(opts.cols,function(i2,item2){
					if(item2.name == val){
						item2.hide = hide;
					}
				});
			});

			var $_tr = '<tr>';
			$.each(opts.cols,function(i,item){
				var align = item.align;
				var width = item.width;
				var name = item.name;
				var title = item.title;

				if(typeof width == 'number'){
					width += 'px';
				}

				if(!item.infoDiv && !item.hide){
					$_tr += '<td style="text-align:'+align+'" width="'+width+'" data-role="'+name+'"></td>';
				}else if(!item.infoDiv && item.hide){
					//$_tr += '<td style="text-align:'+align+';display:none;" width="'+width+'" data-role="'+name+'"></td>';
				}

				if(item.infoDiv){
					that.mname = item.name;
				}
			});

			$_tr += '</tr>';
			var $tr = $($_tr);

			$.each(data,function(i,item){
				//if(i < opts.showLength){
					var $_tr = $tr.clone();

					$_tr.children('td').each(function(ti,titem){
						var name = $(titem).data('role');
						var val = item[name];
						if(name.indexOf('xtime') >=0 && name!="xtime_00" && name!="xtime_03" && val != null){
							val = val.toString().replace('T','  ').replace('+08:00','');
						}
						$(titem).text(val);
						$(titem).attr('title',val);
					})
				//}
				s = item.int08_03;
				if(s == '连接中') statue = 0;
				else if (s == '异常退出') statue = 2;
				else statue = 1;
				
				if(typeof btns == 'object' && btns.length > 0){
					btnShow = true;
					
					if (item.search == undefined && item.int08_00 == 2 ){
						if(statue == 0){
							var len = btns.length-1;
							len = len - 1;
							if(item.int08_12 == 0 && len != 1 && len != 0){
								len = len - 1;
							}
						}else{
							var len = btns.length-2;
							if(item.int08_12 == 0 && len != 1 && len != 0){
								len = len - 1;
							}
						}
					}else if(item.int08_00 == 1){
						var len = btns.length;
						if(item.int08_12 == 0 && len != 1 && len != 0){
							len = len - 1;
						}
                                        }else{
                                                var len = btns.length;
                                                if(item.int08_12 == 0){
                                                        len = len - 1;
                                                }
                                        }
                                         
					btnHtml = $('<div class="tab-ctr" style="width:'+26*len+'px"></div>');
					//m_ses_icon3下载按钮 m_ses_icon6删除按钮 icon-block阻断
					$.each(btns,function(bi,bitem){
						if(item.int08_00 == 2){
							if(statue == 0){
								if(bitem.class == "m_ses_icon3" || bitem.class == "m_ses_icon6" || bitem.class == "m_ses_icon2") return true;
								if(bitem.class == "icon-moni"){
									if(item.int32_01 == 'SSH' || item.int32_01 == 'TELNET' || item.int32_01 == 'RLOGIN' || item.int32_01 == 'RDP' || item.int32_01 == "VNC" || item.int32_01 == "X11" || item.str32_28.indexOf('acc') != -1){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
										$_a.on('click',function(){
											var data = item;
											bitem.cb(data);
										})
									}else{
										var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
									}
								}else if(bitem.class == "msg1"){
									if(item.int08_12 != 0 && item.int08_11 == '未处理'){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
										$_a.on('click',function(){
											var data = item;
											bitem.cb(data,this);
										})
									}else if(item.int08_12 != 0 && item.int08_11 == '已处理'){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
									}else{
										len = len -1;	
									
									}
								}else{							
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data,this);
									})
								}
							}else{
								if(bitem.class == "icon-block" || bitem.class == "icon-moni") return true;
								
								if(bitem.class == "m_ses_icon3"){
									if(item.DownloadEnable == true){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
										$_a.on('click',function(){
											var data = item;
											bitem.cb(data);
										})
									}else{
										var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
									}
								}else if(bitem.class == "m_ses_icon6"){
									if(item.DeleteEnable == true){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
										$_a.on('click',function(){
											var data = item;
											bitem.cb(data);
										})
									}else{
										var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
									}
								}else if(bitem.class == "msg1"){
									if(item.int08_12 != 0 && item.int08_11 == '未处理'){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
										$_a.on('click',function(){
											var data = item;
											bitem.cb(data,this);
										})
									}else if(item.int08_12 != 0 && item.int08_11 == '已处理'){
										var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
									}
								}else{
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data,this);
									})
								}
							}
						}else if(item.int08_00 == 1){
							if(bitem.class == "m_ses_icon3"){
								if(item.DownloadEnable == true){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data);
									})
								}else{
									var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
								}
							}else if(bitem.class == "m_ses_icon6"){
								if(item.DeleteEnable == true){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data,this);
									})
								}else{
									var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
								}
							}else if(bitem.class == "msg1"){
								if(item.int08_12 != 0 && item.int08_11 == '未处理'){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data,this);
									})
								}else if(item.int08_12 != 0 && item.int08_11 == '已处理'){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
								}
								else{
									len = len -1;	
								}
							}else{
								var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
								$_a.on('click',function(){
									var data = item;
									bitem.cb(data,this);
								})
							}
						}else{
							if(bitem.class == "msg1"){
								if((item.int08_12 != 0 && item.int08_12 != null) && (item.int08_11 == '未处理' || item.int08_11 == null)){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
									$_a.on('click',function(){
										var data = item;
										bitem.cb(data,this);
									})
								}else if((item.int08_12 != 0 && item.int08_12 != null) && item.int08_11 == '已处理'){
									var $_a = $('<a href="javascript:;" class="'+bitem.class+' disabled" title="'+bitem.title+'"></a>');
								}
							}else{
								var $_a = $('<a href="javascript:;" class="'+bitem.class+'" title="'+bitem.title+'"></a>');
								$_a.on('click',function(){
									var data = item;
									bitem.cb(data);
								})
							}
						}
						btnHtml.append($_a);
					})
				}
				if(len == 0){
					btnHtml = ""
				}
				if(btnShow){
					$('td:last',$_tr).append(btnHtml);
				}

				if(opts.infoDiv){
					$('td:last',$_tr).append('<div class="tab-moreinfo">'+item[that.mname]+'</div>');
				}

				$body.append($_tr);
			});

			var bw = $body.parents('.xTable').width();
			var tw = $body.parents('table').width();
			if(tw < bw){
				$body.parents('table').width(bw);
			}
			//alert(_global_left);
			$('#tbodyDiv_xTable').scrollLeft(_global_left);	
		},

		_initPage: function(data,type){
			var that = this;
			var $page = this.$page;
			//console.log(_xTable_Data);
			if(type && type == 'page'){
				that.opts.items = _xTable_Data.items;
			}
			
			if(data.totalCount == 0){
				data.totalCount = 0;
			}

			if(data.page == 0){
				data.page = 1;
			}

			var limit = that.opts.data.limit;
			if(!limit){
				limit = 10;
			}
			if(limit>500){
				limit = 500;
			}

			var totalPage = Math.ceil(data.totalCount /  limit);
			if(totalPage == 0){
				totalPage = 1;
			}
			var page = data.page;

			
			$page.html('<div class="totalCountLabel">每页显示<input type="number" value="'+limit+'" name="showLimit" class="showLimit" style="-webkit-ime-mode:Disabled;width:2em;text-align:center;margin:0 4px;">条 总数 '+data.totalCount+' 条</div>');
			var $limit = $page.find('input[name=showLimit]');
			$limit.on('keydown',function(e){
				var number = $(this).val().replace(/[^\d]/g,'');
                $(this).val(number);
			}).on('keyup',function(e){
				var v = $(this).val();
				if(!v || v == 0 || typeof parseInt(v) != 'number'){
					v = 10;
				}
				if(v >500){
					v = 500;
					$(this).val(500);
				}
				var kcode = e.keyCode;
                if(kcode ==  13){
                   $(this).blur();
                }

			}).on('blur',function(e){
				var v = $(this).val();
				if(!v || v == 0 || typeof parseInt(v) != 'number'){
					v = 10;
				}
				if(v >500){
					v = 500;
					$(this).val(500);
				}
				$page.data('limit',v).data('page',1);

                if(v == limit){
                	return;
                }
                that._initBody();
			});

			var $pageList = $('<ul class="pageList"></ul>');

			var $first = $('<li class="first"><i/></li>');
            $pageList.append($first);
            if(page<=1){
                $first.addClass('disable');
            }else{
                $first.on('click', function(){
                    $page.data('page',1);
                    that._initBody();
                });
            }
            var $prev = $('<li class="prev"><i/></li>');
            if(page<=1){
                $prev.addClass('disable');
            }else{
                $prev.on('click', function(){
                	page--;
                    $page.data('page',page);
                    that._initBody();
                });
            }
            $pageList.append($prev);
            var $jump = $('<li class="jump" style="cursor:default;"><input type="number" min="1" max="'+totalPage+'" style="ime-mode:Disabled;" /> / '+ totalPage + '&nbsp;&nbsp;</li>');
            $jump.find('input').val(page);
            $jump.find('input').on('keydown',function(e){
                var number = $(this).val().replace(/[^\d]/g,'');
                $(this).val(number);
            }).on('keyup',function(e){
                var kcode = e.keyCode;
                if(kcode ==  13){
                    $(this).trigger('blur');
                }
            }).on('blur',function(){
            	var v = Number($(this).val().trim());

                if(v > totalPage){
                	v = totalPage;
                }else if(v == 0 || v == 'undefined' || !v){
                	v = 1;
                }
                $page.data('page',v);

                if(v == page){
                	return;
                }
                that._initBody();
				
            });

            $pageList.append($jump);
            var $next = $('<li class="next"><i/></li>');
            var $last = $('<li class="last"><i/></li>');
            if(page>=totalPage){
                $next.addClass('disable');
            }else{
                $next.on('click', function(){
                	page++;
                    $page.data('page',page);
                    that._initBody();
                });
            }
            $pageList.append($next);

            if(page>=totalPage){
                $last.addClass('disable');
            }else{
                $last.on('click', function(){
					$page.data('page',totalPage);
                    that._initBody();
                });
            }
            $pageList.append($last);

			$page.append($pageList);
		},

		_initEvent: function(){
			var that = this;
			var opts = this.opts;
			var $sel = this.$sel;
			var $body = this.$body;

			$sel.on('click','.xTable-head-btn',function(){
				var $_p = $(this).parent();
				var c = $_p.attr('class').split(' ');
				if($.inArray('on',c) >= 0){
					$_p.removeClass('on');

					//that._sortEvent();
				}else{
					$_p.addClass('on');
				}

				$('#tabViewDiv').hide();
				$body.find('tr').removeClass('on');
			});

			$sel.children('.xTable-head-w').hover(function(){
				document.addEventListener('click',function(){
					$sel.children('.xTable-head-w').addClass('on');
				})
			},function(){
				document.addEventListener('click',function(e){
					$sel.children('.xTable-head-w').removeClass('on');

					var $_a = $(e.target);
					$_a = $_a.parents('div.xTable-head-w');
					if($_a.length == 0){
						that._sortEvent();
					}
					
				})
			});

			$sel.on('change','input:checkbox',function(){
				var name = $(this).val();
				var check = $(this).prop('checked');
				var hide = false;
				if(!check){
					hide = true;
				}
				
				var cols = opts.cols;

				$.each(cols,function(i,item){
					if(item.name == name){
						item.hide = hide;
					}
				});
				//改变 checkbox状态要记录到数据库
				console.log(cols);
				ChangeLogFieldStatus(cols);
				
				that.opts.cols = cols;
				that._initHead();
				that._initBody('native');
				//$sel.find('.xTable-head-w').removeClass('on');
			});

			$body.on('mouseover','tr',function(){
				var i = $(this).index();
				var offset = $(this).offset();
				var ao = $body.offset();
				var $ctr = $('.tab-ctr',this);
				var sl = $body.parents('.xTable-body').scrollLeft();
				$ctr.css({
					'top': offset.top - ao.top + $(this).height() - 1 - 40 -1, //40 是table的标题高度
					'left': $body.parents('.xTable-body').width() - $ctr.outerWidth() + sl,
					'height': 15
				})
			});

			if(opts.infoDiv){
				$body.on('click','tr',function(){
					var $_this = $(this);
					var $_infoDiv = $_this.find('div.tab-moreinfo');
					var $_tab = $_this.parents('.xTable-body');

					var c = $_this.attr('class');
					if(c){
						c.split(' ');
					}

					if($('#tabViewDiv').length == 0){
						$('body').append('<div id="tabViewDiv" class="tab-moreinfo" />');
					}

					var $_view = $('#tabViewDiv');

					if(c && $.inArray('on',c) >=0 ){
						$_view.hide();
						$_this.removeClass('on');
						return;
					}

					$_this.addClass('on').siblings().removeClass('on');
					$_view.html($_infoDiv.html()).css({
						'top': $_this.offset().top + $_this.height(),
						'left': $_tab.offset().left,
						'width': $_tab.width()
					}).show();

					var h = $('body').height() - 88;
					var top = $_view.offset().top;
					var height = $_view.outerHeight();
					if(h < top + height){
						$_view.css({
							'top':  $_this.offset().top - height,
						})
					}

					$(window).resize(function(){
						$_view.width($_tab.width() - 38);
					});

					$('.xTable-head-w').removeClass('on');

					$_tab.hover(function(){
						document.onclick = null;
						document.onclick = function(){
							$sel.children('.xTable-head-w').removeClass('on');
						};
					},function(){
						document.onclick = function(){
							$_view.hide();
							$_this.removeClass('on');
						};
					});

					$('div.c-wrap').on('scroll',function(){
						$_view.hide();
						$_this.removeClass('on');
					});
				});
			}

			//
			var $_list = $sel.find('ul')[0];
			Sortable.create($_list,{
				//handle: '.sortBtn'
			});


		},

		_sortEvent: function(){
			var $sel = this.$sel;
			var opts = this.opts;
			var cols = opts.cols;

			var newCols = new Array();
			var check = true;
			$sel.find('li').each(function(i,item){
				var index = $(item).data(index);
				newCols[i] = cols[index.index];
				if(i != index.index){
					check = false;
				}
			});

			if(opts.infoDiv){
				newCols.push(cols[cols.length - 1]);
			}


			if(!check){
				//重新排序
				opts.cols = newCols;
				/*
					$.post(newCols);
				*/
					
				//PChangeLogFieldStatus
				
				console.log(newCols);
				ChangeLogFieldStatus(newCols);
				
				this._initSel();
				this._initHead();
				this._initBody();
			}
		}
	};

	$.fn.xTable = function(){
        if(arguments.length === 0 || typeof arguments[0] === 'object'){
            var option = arguments[0]
                , data = this.data('xTable')
                , options = $.extend(true, {}, $.fn.xTable.defaults, option);
            if (!data) {
                data = new xTable(this, options);
                this.data('xTable', data);
            }
            return $.extend(true, this, data);
        }
        if(typeof arguments[0] === 'string'){
            var data = this.data('xTable');
            var fn =  data[arguments[0]];
            if(fn){
                var args = Array.prototype.slice.call(arguments);
                return fn.apply(data,args.slice(1));
            }
        }
    };

    $.fn.xTable.defaults = {
        width: 'auto'
        , cols: []
        , url: false
        , data: {}
        , method: 'POST'
        , cache: false
        , items: []
        , autoLoad: true
        , remoteSort: false
        , btns: []
        , select: false
        , infoDiv: false
        , showLength: 10
        , showPage: true
		,_global_left:0
    };

    $.fn.xTable.Constructor = xTable;
}(window.jQuery);
