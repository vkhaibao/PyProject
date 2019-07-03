
$(function(){
	$.getScript('/manage/js/md5.js');
	MAX_PAGE = 10;
	/*
	$('.box-table,body,.cont2').on('scroll',function(){
                $('div.tab-moreinfo-on').remove();
                $('tr.on').removeClass('on');
                console.log('scroll');
        })*/
	
	$('.c-cont,.c-cont2').on('scroll',function(event){
		if($("#autoView").is(":visible")){
			$('#autoView').hide();
			$('.g-tsel').children('input').blur();
			$('.g-tsel').removeClass('on');
		}
	})
	$(window).resize(function(){
		if(typeof(from_flag) != 'undefined'){
			if(from_flag == 'search')$('#tbodyDiv_xTable').height($('body').height()-258 + 36);
			else $('#tbodyDiv_xTable').height($('body').height()-258);
		}else{
			$('#tbodyDiv_xTable').height($('body').height()-258);
		}

		$('.xTable-body-wrapper').height($('#tbodyDiv_xTable').height() + 40)
        });
	/*
	$('input.datepicker').on('click',function(){
		if($('div.datepick-popup').length > 0)	
                	$('div.datepick-popup').show();
        })*/

})

function _alert(i,title,result,obj,url){
	obj = obj || $('#_');
	url = url || "";
	if(i == 0){
		class_name = 'alert succ';
	}else if( i == 1){
		class_name = 'alert fail';
	}else if(i == 2){
		class_name = 'alert warning';
	}
	$('.btn').blur();
	$(obj).blur();	
	//$('.filter-btn').blur();
	//$('.layui-layer-btn a').focus();
	$('.layui-layer-btn-c a').focus();
	if($('#mframe',parent.document).length >0 || $('#sFrame',parent.parent.document).length >0 || $('#iframe_task',parent.parent.document).length >0 || $('#bbTarget',parent.document).length >0 || $('#ywTarget',parent.document).length > 0){
		index = parent.parent.parent.layer.open({
			type:1,
			title:title,
			content:'<div class="layer-alert"><i class="'+class_name+'"></i>'+result+'</div>',
			btn:['确&nbsp;&nbsp;定'],
			btnAlign:'c',
			/*closeBtn: false,*/
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				parent.parent.parent.layer.close(i);
				obj.focus();
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
			        }else{
					if(url !=""){
						location.href = url;
					}
				}

			},
			cancel: function(i){
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
				}
            },success: function(i){
				$(document).unbind('keydown').bind('keydown', function(e) {
					e = e || window.event;
					if(e.keyCode == 13) {
						var target = e.target || e.srcElment;
						if(target.id ==''){
							if($(".layui-layer-close").is(":visible")==true){
								parent.parent.layer.close(index);
							}       
						}
					}
				});
			}
		});
	}else{
		index = parent.parent.layer.open({
			type:1,
			title:title,
			content:'<div class="layer-alert"><i class="'+class_name+'"></i>'+result+'</div>',
			btn:['确&nbsp;&nbsp;定'],
			btnAlign:'c',
			/*closeBtn: false,*/
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				parent.parent.layer.close(i);
				obj.focus();
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
					top.location.href='/';
			        }else{
                                        if(url !=""){
                                                location.href = url;
                                        }
                                }


			},
			cancel: function(i){
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
				}
            },success: function(i){
				$(document).unbind('keydown').bind('keydown', function(e) {
					e = e || window.event;
					if(e.keyCode == 13) {
						var target = e.target || e.srcElment;
						if(target.id ==''){
							if($(".layui-layer-close").is(":visible")==true){
								parent.parent.layer.close(index);
							}       
						}
					}
				});
			}
		});

	}
}

function _alert2(i,title,result,obj,url){
	obj = obj || $('#_');
	url = url || "";
	if(i == 0){
		class_name = 'alert succ';
	}else if( i == 1){
		class_name = 'alert fail';
	}else if(i == 2){
		class_name = 'alert warning';
	}
	$('.btn').blur();
	$(obj).blur();	
	//$('.filter-btn').blur();
	//$('.layui-layer-btn a').focus();
	$('.layui-layer-btn-c a').focus();
	if($('#mframe',parent.document).length >0 || $('#sFrame',parent.parent.document).length >0 || $('#iframe_task',parent.parent.document).length >0 || $('#bbTarget',parent.document).length >0 || $('#ywTarget',parent.document).length > 0){
		index = parent.parent.parent.layer.open({
			type:1,
			title:title,
			content:'<div class="layer-alert"><i class="'+class_name+'"></i>'+result+'</div>',
			btn:['确&nbsp;&nbsp;定'],
			btnAlign:'c',
			/*closeBtn: false,*/
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				parent.parent.parent.layer.close(i);
				obj.focus();
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
			        }else{
					if(url !=""){
						location.href = url;
					}
				}

			},
			cancel: function(i){
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
				}
            }
		});
	}else{
		index = parent.parent.layer.open({
			type:1,
			title:title,
			content:'<div class="layer-alert"><i class="'+class_name+'"></i>'+result+'</div>',
			btn:['确&nbsp;&nbsp;定'],
			btnAlign:'c',
			/*closeBtn: false,*/
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				parent.parent.layer.close(i);
				obj.focus();
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
					top.location.href='/';
			        }else{
                                        if(url !=""){
                                                location.href = url;
                                        }
                                }


			},
			cancel: function(i){
				if(result.indexOf('系统繁忙')>=0 || result.indexOf('非法访问')>=0 || result.indexOf('系统超时') >=0){
                			top.location.href='/';
				}
            }
		});

	}
}

function regCheck(obj,nameReg){
	var val = $(obj).val();
	var $i = $(obj).next('i.v-check')
	var o = $i.parent().parent().find('em')
	if(val == "" && o.length ==0){
		
		$i.hide();
		return false;
	}
	if(nameReg.test(val)){
		$i.show().attr('class','v-check v-right');
	}else{
		$i.show().attr('class','v-check v-wrong');
	}
}



function HTMLEncode(str){
	var newStr = "";
	if(!str){
		return "";
	}
	newStr = str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;").replace(/ /g, "&nbsp;").replace(/\n/g," ");
	return newStr;
}

/*
function tabArr(){
	$('table').unbind();
	var $infodiv;
	$('table').on('mouseover','a.tab-arr',function(){
		var $tr = $(this).parents('tr');
		var oset = $tr.offset();
		$infodiv = $(this).parent().next('div.tab-moreinfo').clone().appendTo('body');
		$infodiv.css({
			top:oset.top + $tr.outerHeight() + 1,
			left:oset.left,
			width:$tr.outerWidth() - 1
		}).stop().slideDown(200);
	}).on('mouseover','div.tab-moreinfo',function(){
		$infodiv.stop().show();
	}).on('mouseout','tr',function(){		
		if($infodiv){
			//console.log($infodiv);
			$infodiv.stop().remove();
		}
	});

	var len = $('.tab-ctr:first').children('a').length;
	$('table>thead>tr>th:last').width(len*24);
}
*/
/*
function tabArr(){
	var tout,tin;
	var $cloneItem;
	$('table').on('mouseover','a.tab-arr',function(){
		clearTimeout(tout);
		var $this = $(this);
		tin = setTimeout(function(){
			var $tr = $this.parents('tr');
			var oset = $tr.offset();
			
			var $box = $this.parents('div.box-table');
			var boxh = $box.outerHeight(), boxo = $box.offset();

			var $item = $this.parent().next('div.tab-moreinfo');
			var ih = $item.outerHeight(),th = $tr.outerHeight();

			$cloneItem = $item.clone().appendTo('body');

			if(boxh < oset.top-boxo.top + ih + th ){
				$cloneItem.css({
					top:oset.top - ih,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});
			}else{
				$cloneItem.css({
					top:oset.top + $tr.outerHeight() + 1,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});
			}
		},200);
		
	}).on('mouseout','tr',function(){
		clearTimeout(tin);
		tout = setTimeout(function(){
			if($cloneItem){
				$cloneItem.remove();
			}
		},50);
	});

	$('div.tab-moreinfo').hover(function(){
		clearTimeout(tout);
		$(this).stop().show();
	},function(){
		clearTimeout(tin);
		tout = setTimeout(function(){
			if($cloneItem){
				$cloneItem.remove();
			}
		},50);
	});
}
*/
function tabArr(){
	$('table').unbind();
	var tout,tin;
	var $cloneItem;
	var z = false;

	$('table').on('mouseover','tbody>tr',function(){
		document.onclick = null;
	}).on('mouseout','tbody>tr',function(){
		document.onclick = function(){
			$('div.tab-moreinfo-on').hide();
			$('tr.on').removeClass('on');
		}
	}).on('click','tbody>tr',function(e){
		/*
		z = false;
		if($('div.tab-moreinfo-on').is(':visible')){
			$('div.tab-moreinfo-on').remove();
			var c = $(this).parents('tr').attr('class');
			if(c && c.indexOf('on') >= 0){
				z = true;
			}
			$(this).parents('tbody').children('tr').removeClass('on');
		}

		if(z){
			return;
		}
		*/
		x=e.target;
		if(x.id=='del'){
			return false;
		}
		if(x.id=='edit'){
			return false;
		}
		if (x.localName=='a'){
			return false;
		}
		document.onclick = null;

		//clearTimeout(tout);
		var $this = $(this);
		//tin = setTimeout(function(){
			//var $tr = $this.parents('tr');
			var $tr = $this;
			var oset = $tr.offset();

			var trc = $tr.attr('class');
			if(trc && trc.indexOf('on') >=0 ){
				$('div.tab-moreinfo-on').hide();
				$('tr.on').removeClass('on');
				return;
			}

			$('div.tab-moreinfo-on').hide();
			$('tr.on').removeClass('on');
			$tr.addClass('on');
			
			//var $box = $this.parents('div.box-table');
			var $box = $this.parents('div.box-table').parents('.c-cont');
			//var boxh = $box.outerHeight(), boxo = $box.offset();
			var boxh = $box.height() - 40, boxo = $box.offset();

			var $item = $this.children('td:last').children('div.tab-moreinfo');
			var ih = $item.outerHeight(),th = $tr.outerHeight();

			$cloneItem = $item.clone().addClass('tab-moreinfo-on').appendTo('body');

			if(boxh < oset.top-boxo.top + ih + th - 40 ){
				$cloneItem.css({
					top:oset.top - ih,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});

				var iof = $cloneItem.offset().top + $cloneItem.outerHeight();
				var tof = $tr.offset().top;
				if(iof != tof){
					$cloneItem.css('top',$tr.offset().top - $cloneItem.outerHeight());
				}
			}else{
				$cloneItem.css({
					top:oset.top + $tr.outerHeight() + 1,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});
			}
		//},200);
	})/*.on('mouseout','tr',function(){
		clearTimeout(tin);
		tout = setTimeout(function(){
			if($cloneItem){
				$cloneItem.remove();
			}
		},50);
	})*/;

	/*
	$('div.tab-moreinfo').hover(function(){
		clearTimeout(tout);
		$(this).stop().show();
	},function(){
		clearTimeout(tin);
		tout = setTimeout(function(){
			if($cloneItem){
				$cloneItem.remove();
			}
		},50);
	});
	*/
	
	$('.box-table,body,.c-cont2,.c-cont').on('scroll',function(){
		$('div.tab-moreinfo-on').remove();
		$('tr.on').removeClass('on');
	})
	
	//var len = $('.tab-ctr:first').children('a').length;
	//$('table>thead>tr>th:last').width(len*24);
}

function DigitInput(e) {
    var e = e || window.event; //IE、FF下获取事件对象
    var cod = e.charCode||e.keyCode; //IE、FF下获取键盘码
     if((cod!=8 && cod != 9 && cod != 46 && cod!=13 && (cod<37 || cod>40) && (cod<48 || cod>57) && (cod<96 || cod>105))){
        notValue(e);
    }else{      
       if(e.shiftKey){
         notValue(e);
       }
	}
    function notValue(e){
        e.preventDefault ? e.preventDefault() : e.returnValue=false;
    }
}
var loadLayer = false;
function _showLoading(flag){
	var arclist = arguments;
    loadLayer = layer.open({
        title:false,
        closeBtn:false,
        content:'<div id="Loading"></div>',
        btn:false,
        skin:'loadingbar',
        area:['250px','250px'],
        move:false,
        resize:false,
	isOutAnim: false,
        shade:[0.1,'#000'],
        success:function(){
			if(flag == "get_hostdirectory") get_hostdirectory(arclist[1],arclist[2]);
        }
    })
}
function _closeLoading(){
	if(loadLayer)
		layer.close(loadLayer);
}

function tabArr1(){
	$('table').unbind();
	var tout,tin;
	var $cloneItem;
	var z = false;
	////console.log("asdadad");

	$('table').on('mouseover','tbody>tr',function(){
		document.onclick = null;
	}).on('mouseout','tbody>tr',function(){
		document.onclick = function(){
			$('div.tab-moreinfo-on').hide();
			$('tr.on').removeClass('on');
		}
	}).on('click','tbody>tr',function(e){		
		x=e.target;
		if(x.id=='del'){
			return false;
		}
		if(x.id=='edit'){
			return false;
		}
		if(x.localName=='a'){
			return false;
		}
		document.onclick = null;

		var $this = $(this);

			var $tr = $this;
			////console.log("123133");
			////console.log($tr);
			var oset = $tr.offset();
			////console.log(oset);
			var trc = $tr.attr('class');
			if(trc && trc.indexOf('on') >=0 ){
				$('div.tab-moreinfo-on').hide();
				$('div.tab-moreinfo-on').remove();
				$('tr.on').removeClass('on');
				return;
			}

			$('div.tab-moreinfo-on').hide();
			$('tr.on').removeClass('on');
			$tr.addClass('on');
			
			var $box = $this.parents('div.box-table');
			////console.log($box);
			var boxh = $box.outerHeight(), boxo = $box.offset();
			////console.log("boxh:"+ boxh);
			////console.log("boxo:"+boxo);
			var $item = $this.children('td:last').children('div.tab-moreinfo');
			////console.log($item);
			var ih = $item.outerHeight(),th = $tr.outerHeight();
			////console.log("ih:"+ih);
			////console.log("th:"+th);
			$cloneItem = $item.clone().addClass('tab-moreinfo-on').appendTo('body');
			////console.log("oset.top:"+oset.top);
			////console.log("boxo.top:"+boxo.top);

			boxh = parseInt(boxh);
			var hcheck = parseInt(oset.top-boxo.top + ih + th - 40);

			if(boxh < hcheck ){
				$cloneItem.css({
					top:oset.top - ih,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});

				var iof = $cloneItem.offset().top + $cloneItem.outerHeight();
				var tof = $tr.offset().top;
				if(iof != tof){
					$cloneItem.css('top',$tr.offset().top - $cloneItem.outerHeight());
				}
			}else{
				$cloneItem.css({
					top:oset.top + $tr.outerHeight() + 1,
					left:oset.left,
					width:$tr.outerWidth() - 1,
					opacity:0,
					display:'block'
				}).stop().animate({
					opacity:1
				});
			}
			//$cloneItem.prev('div').remove();
			z_v = $cloneItem.prev('div').css('z-index');
			$cloneItem.css('z-index',z_v+1);
	});
	$('.box-table,body,.c-cont2,.c-cont').on('scroll',function(){
		$('div.tab-moreinfo-on').remove();
		$('tr.on').removeClass('on');
	})
	
	//var len = $('.tab-ctr:first').children('a').length;
	//$('table>thead>tr>th:last').width(len*24);
}
function alertError(type,se,uCode){
	type = type || "bhost";
	se = se || '';
	uCode = uCode || '';
	var checkg = false;
	if(se != '' || uCode !=''){
		var isMac = (navigator.platform == "Mac68K") || (navigator.platform == "MacPPC") || (navigator.platform == "Macintosh") || (navigator.platform == "MacIntel");
		if(isMac) return 0;
		$.ajax({
			url: '/bhost/GetNoAlert',
			type: 'post',
			async: false,
			data: { a0: se,a1:uCode},
			success: function (result) {
				var result=JSON.parse(result);
				
				if(result.Result){
					result = result.info;
					if(result == '1'){
						checkg = true;
					}
				}else{
					_alert(2,"更新客户端",result.ErrMsg);
					return false;
				}
			}
		})
	}else{
		return 0;
	}
	var title = '检测到未安装客户端或请求被拦截，请检查';
	if(type == 'bhost') {	
		var content ='<div class="layer-alert"><i class="alert warning"></i><span>'+title+'</span></div>';
	}
	else {
		var content ='<div class="layer-alert"><i class="alert warning"></i><span>'+title+'</span><div style="margin-top: 5px;"><input type="checkbox" class="form-checkbox" name="" id="layer_div" value="" >不再提示</div></div>';
	}
	//
	if(loadLayer_client) parent.parent.layer.close(loadLayer_client);
	
	if(checkg || type.toLowerCase() =='bhost'){
		 parent.parent.layer.open({
			type:1,
			title:"运维客户端",
			content:content,
			btn:['下&nbsp;&nbsp;载', '取&nbsp;&nbsp;消'],
			btnAlign:'c',
			closeBtn: false,
			skin:'layer-custom',
			area:['380px','310px'],
			move: false,
			resize: false,
			btn1:function(i){
				 parent.parent.layer.close(i);
				var splatform = navigator.platform;
				if(splatform.indexOf("Mac") > -1){
					location.href = '/bhost/download_BHostClient_zip';
				}else{
					location.href='/bhost/download_BHostClient_exe';	
				}
				if(type.toLowerCase() !='bhost') NoAlert(se,uCode);
			},
			btn2:function(i){
				parent.parent.layer.close(i);
				if(type.toLowerCase() !='bhost') NoAlert(se,uCode);
			},success: function(i){
				if(type.toLowerCase() =='bhost') $('#layer_div').parent().remove();
				else{
					$('#layer_div').iCheck({
						checkboxClass: 'icheckbox_minimal-blue',
						radioClass: 'iradio_minimal-blue',
						increaseArea: '0' // optional
					});
					$('.layer-alert .warning').css('height',"110px");
				}
			}
		});
	}
}
function NoAlert(se,uCode){
	//不在提示
	$.ajax({
		url: '/bhost/UpdateNoAlert',
		type: 'post',
		async: false,
		data: { a0: se ,a1:$('#layer_div').prop("checked")?0:1,a2:uCode},
		success: function (result) {		
		}
	})
}
	
function get_regedit(typ,se,uCode,sesstimet){
	se = se || '';
	uCode = uCode || '';
	//插入数据库数据
	$.ajax({
		url: "/bhost/insert_usbkeys",
		type:"POST",
		async:false,		
		data:{a0:se,z1:sesstimet,t1:"IfUpdate",u1:' ',c1:' ',a10:""},
		success:function(result){
			var result=JSON.parse(result);
			if(result.Result){
			}else{
				_alert(1,"检查客户端",result.ErrMsg);
				if(window.parent.parent.document.frm.use_BH!=undefined)window.parent.parent.document.frm.use_BH.value='0';
				return false;
			}
		}
	})		
	//循环获取 数据库状态
	var c = 0;		
	var if_ok_down_other = setInterval(function(){
		ret = repeat_get_path_other(sesstimet,se);
		
		if(ret[0] == 1 && ret[1].toLowerCase() =='true' ){
			if(window.parent.parent.document.frm.use_BH!=undefined) window.parent.parent.document.frm.use_BH.value='1';
			if((typeof check_cilent) != undefined) check_cilent = true;
			clearInterval(if_ok_down_other);
			return 0;				
		}
		if(c >=10){
			if(window.parent.parent.document.frm.use_BH!=undefined)window.parent.parent.document.frm.use_BH.value='0';
			clearInterval(if_ok_down_other);	
			alertError(typ,se,uCode);
			return 0;
		}			
		c = c + 1;				
	},500)
}
function repeat_get_path_other(sesstimet,se){
	var st = 0;
	$.ajax({
		url: "/bhost/repeat_get_path",
		type:"POST",
		async:false,		
		data:{a0:se,z1:sesstimet},
		success:function(result){
			var result=JSON.parse(result);
			if(result.Result){
				st = result.info;
				absolute_path = result.path;
			}else{
				_alert(1,"检查客户端",result.ErrMsg);
				return false;
			}
		}
	})
	return [st,absolute_path];
}
function aceg(a,b){
	mstr=$.md5(a).split('');
	$(mstr).each(function(i,item){
		if(i == 15) mstr[i] = mstr[i] +b;
	})
	ms = mstr.join('');
	return $.md5(ms)
}
