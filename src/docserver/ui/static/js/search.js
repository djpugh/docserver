
$(document).ready(function() {
 var params = (new URL(document.location)).searchParams;
 if (params.has('q')){
    $("input#main-search-box").val(params.get('q'))
    search(params.get('q'))
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
          var item_tags = '<span class="badge badge-info ml-1">'+store[ref].tags.split(";").join('</span><span class="badge badge-info ml-1">')+'</span>'
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
            store[ref].body +
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