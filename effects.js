// JavaScript Document
$(function(){
     var len  = $("#numeric > li").length;
	 var index = 0;
	 $("#numeric li").mouseover(function(){
		index  =   $("#numeric li").index(this);
		rotatorimg(index);
	});
	 $("#timer").hover(function(){
			  if(MyTime){
				 clearInterval(MyTime);
			  }
	 },function(){
			  interval = setInterval(function(){
			    rotatorimg(index)
				index++;
				if(index==len){index=0;}
			  } , 2000);
	 });
	 var interval = setInterval(function(){
		rotatorimg(index)
		index++;
		if(index==len){index=0;}
	 } , 10000);
})
function rotatorimg(i){
		$("#slider").stop(true,false).animate({top : -188*i},800);
		$("#numeric li").eq(i).addClass("on").siblings().removeClass("on");
}
function goTopEx(){
        var obj=document.getElementById("goTopBtn");
        function getScrollTop(){
                return document.body.scrollTop;
            }
        function setScrollTop(value){
                document.body.scrollTop=value;
            }
        window.onscroll=function(){getScrollTop()>0?obj.style.display="":obj.style.display="none";}
        obj.onclick=function(){
            var goTop=setInterval(scrollMove,10);
            function scrollMove(){
                    setScrollTop(getScrollTop()/1.1);
                    if(getScrollTop()<1)clearInterval(goTop);
                }
        }
    }
  goTopEx();
