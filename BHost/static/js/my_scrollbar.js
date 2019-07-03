(function (win,dom) {

    function MyScrollBar(o) {
        this.init(o);
    }
    MyScrollBar.prototype={
        init:function (o) {
            this.scrollLeft=0;  //滚动内容的X轴滚动距离
            this.barShow=false; //是否显示滚动条

            this.wrapper=document.getElementById(o.selId);
            this.content=this.wrapper.firstElementChild;
            this.addScroll();

            this.initState(); //设置初始状态
            this.initEvent();   //设置事件函数
        },

        //判断是否添加滚动条
        addScroll:function () {
            //获取包裹层与滚动层的尺寸;
            this.getSize();

            if(this.iWrapperW<=this.iScrollW){
                this.barShow=true;

                this.oxBox=dom.createElement('div');
                this.oxBar=dom.createElement('div');
                this.oxBox.appendChild(this.oxBar);
                this.wrapper.insertBefore(this.oxBox,this.content);

            }
        },
        getSize:function () {

            this.iWrapperW=this.wrapper.offsetWidth;
            this.iScrollW=this.content.offsetWidth;
            this.scrollboxw=this.iWrapperW;

            this.barw=this.iWrapperW/this.iScrollW*this.iWrapperW;
        },

        initState:function () {
            if(this.barShow){

                setStyle(this.oxBox,{
                    display:'none',
                    position:'absolute',
                    bottom:0,
                    left:0,
                    zIndex:10,
                    width:'100%',
                    height:'6px',
                    backgroundColor:'#eaeaea'
                });
                setStyle(this.oxBar,{

                    position:'absolute',
                    bottom:0,
                    left:0,
                    height:"100%",
                    width:this.barw+'px',
                    backgroundColor:'#ccc',
                    borderRadius:'3px'
                })
            }
        },
        initEvent:function () {
            var _this=this;
            var isIn=false;
            if(this.barShow){
                this.wrapper.onmouseenter=function () {
                    isIn=true;

                    setStyle(_this.oxBox,{
                        display:'block'
                    })
                }

                this.wrapper.onmouseleave=function () {
                    isIn=false;

                    setStyle(_this.oxBox,{
                        display:'none'
                    })
                }

            }

            var ixbarleft=0,bxDown=false,bxleave=true,iDownPageX;
            if(this.barShow){
                this.oxBar.onmousedown=function (e) {
                    bxDown=true;
                    iDownPageX=e.clientX+dom.documentElement.scrollLeft||dom.body.scrollLeft;

                    ixbarleft=parseInt(getStyle(this,'left'));
                    canSelectText(false);

                }
            }

            dom.addEventListener('mouseup',function () {

                bxDown=false;
                canSelectText(true);
                if(!isIn && this.barShow){
                    setStyle(_this.oxBox,{
                        display:'none',
                    })
                }

            })

            dom.addEventListener('mousemove',function (e) {
                if(bxDown && _this.barShow){

                    var iNowPageX=e.clientX+dom.documentElement.scrollLeft||dom.body.scrollLeft;
                    var iNowLeft=ixbarleft+iNowPageX-iDownPageX;
                    iNowLeft=iNowLeft<=0?0:iNowLeft>=_this.scrollboxw-_this.barw?_this.scrollboxw-_this.barw:iNowLeft;
                    _this.scrollLeft=iNowLeft*_this.scrollboxw/_this.barw;

                    _this.setTranslate();
                    _this.setXLeft(iNowLeft);
                }
            })
            if(this.barShow){
                this.oxBar.ondrag=function (e) {
                    var e=evt||win.event;
                    evt?e.preventDefault():e.returnValue=false;
                }
            }

        },
        setTranslate:function (iTime) {
            var sTranslate='translate(-'+this.scrollLeft+'px, -'+0+'px)';

            setStyle(this.content,{
                transition:iTime>=0?iTime+'ms ease-in-out':0+'ms',
                transform:sTranslate,
                msTransform:sTranslate,
                webkitTransform:sTranslate,
                mozTransform:sTranslate,
                oTransform:sTranslate
            })
        },
        setXLeft:function (iLeft,iTime) {
            setStyle(this.oxBar,{
                transition:iTime>=0?iTime+'ms ease-in-out':0+'ms',
                left:iLeft+'px'
            })
        }

    }
    function getStyle(obj,name) {
        if(win.getComputedStyle){
            return getComputedStyle(obj,null)[name]
        }else {
            return obj.currentStyle[name];
        }
    }
    function setStyle(obj,style) {
        for(var i in style){
            obj.style[i]=style[i];
        }
    }

    function canSelectText(bole) {
        if(!bole){
            dom.body.style.mozUserSelect='none';
            dom.body.style.webkikUserSelect='none';
            dom.body.style.msUserSelect='none';
            dom.body.style.khtmlUserSelect='none';
            dom.body.style.userSelect='none';
        }else {
            dom.body.style.mozUserSelect='text';
            dom.body.style.webkikUserSelect='text';
            dom.body.style.msUserSelect='text';
            dom.body.style.khtmlUserSelect='text';
            dom.body.style.userSelect='text';
        }
    }
    win.MyScrollBar=MyScrollBar;
})(window,document)
