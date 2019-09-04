
$(document).ready(function() {
 var params = (new URL(document.location)).searchParams;
 if (params.has('q')){
    $("input#main-search-box").val(params.get('q'))
    search(params.get('q'))
 }

 function formatContent(content, searchTerm){
    var termIdx = content.toLowerCase().indexOf(searchTerm.toLowerCase());
    if (termIdx >= 0){
        var startIdx = Math.max(0, termIdx - 140);
        var endIdx = Math.min(content.length, termIdx + searchTerm.length + 140);
        var trimmedContent = (startIdx === 0) ? "" : "&hellip;";
        trimmedContent += content.substring(startIdx, endIdx);
        trimmedContent += (endIdx >= content.length) ? "" : "&hellip;";

        var highlightedContent = trimmedContent.replace(new RegExp(searchTerm, 'ig'), function matcher(match){
            return "<strong>"+match+"</strong>";
            });
        return highlightedContent;
    }else{
        var emptyTrimmedString = content.substr(0, 280);
        emptyTrimmedString += (content.length < 280) ? "" : "&hellip;"
        return emptyTrimmedString
    }
 }

 function search(query){
    var result = idx.search(query);
    var resultdiv = $("#results");
    // Show results
    resultdiv.empty();
    // If no results
    if (result.length === 0){
        resultdiv.append('<div class="no-result">No results found</div>')
    } else{
        for (var item in result) {
          var ref = result[item].ref;
          var item_tags = ""
          for (var tagIdx in store[ref].tags){
            var tag = store[ref].tags[tagIdx]
            item_tags +='<a href=/search?q=tags:'+tag+'><span class="badge badge-info ml-1">'+tag+'</span></a>'
          }
          if (store[ref].repository.startsWith('http')){
              var repo_tag = '<a href="'+
                             store[ref].repository +
                             '"><span class="badge badge-primary ml-1">Source</span></a>'
          }else{
          var repo_tag = ''
          }
          var searchitem =
            '<div class="row">'+
            '<div class="col-xl-10 result">'+
            '<div class="results-header">'+
            '<h3 style="display: inline">'+
            '<a href="' +
            store[ref].link +
            '" class="page_name">' +
            store[ref].title +
            '</a></h3>' +
            '  <a href="' +
            store[ref].root_url +
            '"><span class="badge badge-secondary ml-2">' +
            store[ref].name +
            " (" +
            store[ref].version +
            ')</span></a> ' +
            item_tags +
            "</div><div class='excerpt'><p>" +
            formatContent(store[ref].body, query)+
            "</p></div></div></div>";
          resultdiv.append(searchitem);
        }
     }
 }
  $("input#main-search-box").on("keyup", function() {
    // Get query
    var query = $(this).val();
    // Search for it
    search(query)
  });

});