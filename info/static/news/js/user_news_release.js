function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {

    $(".release_form").submit(function (e) {
        e.preventDefault()

             // 发布新闻
        $(this).ajaxSubmit({
            beforeSubmit:function f(request){
                for (var i=0;i<request.length;i++){
                    var item = request[i]
                    if (item["name"] == "content"){
                        item["value"] = tinyMCE.activeEditor.getContent()
                    }
                }
            },
            url: "/profile/news_release",
            type: "POST",
            headers: {
                "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == "0") {
                    // 选中索引为6的左边单菜单
                    alert(resp.errmsg)
                    window.parent.fnChangeMenu(6)
                    // 滚动到顶部
                    window.parent.scrollTo(0, 0)
                }else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})