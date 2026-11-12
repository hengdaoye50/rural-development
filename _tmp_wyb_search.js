//搜索    
function query() {
	var searchTerm = jQuery.trim($("#textboxs").val());
	if (searchTerm) {
		// 保存搜索历史到独立存储
		saveSearchHistory(searchTerm);
		
		// 确保隐藏字段与输入框同步
		$("#keyWordsHidden").val(searchTerm);
		// 确保以 POST 方式提交 keyWords（避免上一次提交移除了 name 导致本次未提交）
		$("#keyWordsHidden").attr("name", "keyWords");
	
		$("#searchForm").submit();
	}
}

// 保存搜索历史
function saveSearchHistory(term) {
    if (term.trim()) {
        var searchHistory = JSON.parse(localStorage.getItem('thirdPartySearchHistory')) || [];
        if (searchHistory.indexOf(term) === -1) {
            searchHistory.push(term);
            if (searchHistory.length > 10) {
                searchHistory.shift();
            }
            localStorage.setItem('thirdPartySearchHistory', JSON.stringify(searchHistory));
        }
    }
}
//热搜词
function queryByHotWord(hotWord) {
	$("#textboxs").val(hotWord);
	// 确保隐藏字段正确设置
	$("#keyWordsHidden").val(hotWord);
	// 确保以 POST 方式提交 keyWords（避免被移除 name）
	$("#keyWordsHidden").attr("name", "keyWords");
	// 保存到独立的搜索历史
	saveSearchHistory(hotWord);
	
	$("#searchForm").submit();
}

$(function(){
	var params = new URLSearchParams(window.location.search);
	if (params.get('regionCode')) {
		$("#regionId").val(params.get('regionCode'));
	}
    //回车搜索
	$("#textboxs").keyup(function() {
		var searchInput = jQuery.trim($(this).val());
		var rule = /[>&$#<\/\\]/ig;
		if (rule.test(searchInput)) {
			$(this).val(searchInput.replace(rule, ''));
		}
	})

    //为空不允许跳转，3秒后自动隐藏提示框
    let timeoutId;
    $("#searchForm").on("keypress", function(event) {
        if(event.key === "Enter" || event.keyCode === "13"){
            event.preventDefault();
            const searchInput = jQuery.trim($("#textboxs").val());
            const $alertBox = $("#alertBox");

            var rule = /[>&$#<\/\\]/ig;
            if(rule.test(searchInput)){
                $("#textboxs").val(searchInput.replace(rule,''));
            }
            if(searchInput === "") {
                $alertBox.show();
                clearTimeout(timeoutId); 
                timeoutId = setTimeout(function() {
                    $alertBox.hide();
                }, 3000);
            }else{
               query();
            }
        }
    });
    $('#wrappers .group').on("click", function(event) {
        const searchInput = jQuery.trim($("#textboxs").val());
        const $alertBox = $("#alertBox");
        if (searchInput === "") {
           $alertBox.show();
           clearTimeout(timeoutId); 
           timeoutId = setTimeout(function() {
               $alertBox.hide();
           }, 3000);
        }else{
           query();
        }
    });
})    