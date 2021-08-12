/* global tableau */

let app_name;
let myConnector = tableau.makeConnector();

myConnector.getSchema = schemaCallback => {
  let reviewCols = [
    {
      id: "reviewId",
      alias: "Review ID",
      dataType: "string"
    },
    {
      id: "userName",
      alias: "User Name",
      dataType: "string"
    },
    {
      id: "userImage",
      alias: "User Image Link",
      dataType: "string"
    },
    {
      id: "content",
      alias: "Review Content",
      dataType: "string"
    },
    {
      id: "score",
      alias: "Review Score",
      dataType: "int"
    },
    {
      id: "thumbsUpCount",
      alias: "Thumb Up Count",
      dataType: "int"
    },
    {
      id: "at",
      alias: "Created At",
      dataType: "datetime"
    },
    {
      id: "replyContent",
      alias: "Response",
      dataType: "string"
    },
    {
      id: "repliedAt",
      alias: "Replied At",
      dataType: "datetime"
    },
    {
      id: "reviewCreatedVersion",
      alias: "For which version",
      dataType: "float"
    },
    {
      id: "sentimentScore",
      alias: "Sentiment Score",
      dataType: "float"
    }
  ];

  let all_reviewsSchema = {
    id: "all_reviews",
    alias: "All reviews",
    columns: reviewCols
  };

  let tokenizedreviewCols = [
    {
      id: "reviewId",
      alias: "Review ID",
      dataType: "string"
    },
    {
      id: "tokenizedReview",
      alias: "Tokenized reviews",
      dataType: "string"
    }
  ];

  let tokenized_reviewSchema = {
    id: "tokenized_review",
    alias: "Tokenized Review",
    columns: tokenizedreviewCols
  };

//Steven 08JUL2021 starts add the standard connection
var standardConnection = {
    "alias": "Joined GooglePlay reviews data",
    "tables": [{
        "id": "all_reviews",
        "alias": "All reviews"
    }, {
        "id": "tokenized_review",
        "alias": "Tokenized Review"
    }],
    "joins": [{
        "left": {
            "tableAlias": "All reviews",
            "columnId": "reviewId"
        },
        "right": {
            "tableAlias": "Tokenized Review",
            "columnId": "reviewId"
        },
        "joinType": "inner"
    }]
};
//Steven 08JUL2021 ends
  schemaCallback([all_reviewsSchema, tokenized_reviewSchema], [standardConnection]);
  //schemaCallback([all_reviewsSchema]);
};

myConnector.getData = (table, doneCallback) => {
  //console.log("In getData");
  let connectionData = JSON.parse(tableau.connectionData);
  let app_name = connectionData.app_name;
  console.log("app_name "+app_name);
  let tableData = []; //for review
  const Url = `http://10.108.22.222:5000/?app_name=${app_name}`; //CHANGE HERE TO THE IP OF SERVER IN WHICH SCRAPE SCRIPT IS RUNNING

  $.get(Url,function(response) {
  //as the response is the String type, we need to convert it into JSON
  const res_in_json = JSON.parse(response);
  //console.log("now res_in_json -->"+res_in_json);
   
    if (table.tableInfo.id === "all_reviews") {
      for (var key in res_in_json) {
        if (res_in_json.hasOwnProperty(key)) {
          // here you have access to
          var reviewId = res_in_json[key].reviewId;
          var userName = res_in_json[key].userName;
          var userImage = res_in_json[key].userImage;
          var content = res_in_json[key].content;
          var score = res_in_json[key].score;
          var thumbsUpCount = res_in_json[key].thumbsUpCount;
          var reviewCreatedVersion = res_in_json[key].reviewCreatedVersion;
          var at = res_in_json[key].at;
          var replyContent = res_in_json[key].replyContent;
          var repliedAt = res_in_json[key].repliedAt;
          //steven starts
          var sentimentscore = res_in_json[key].sentiment_score;
          //steven ends
          tableData.push({
            reviewId: reviewId,
            userName: userName,
            userImage: userImage,
            content: content,
            score: score,
            thumbsUpCount: thumbsUpCount,
            reviewCreatedVersion: reviewCreatedVersion,
            at: at,
            replyContent: replyContent,
            repliedAt: repliedAt,
            sentimentScore: sentimentscore
          });
        }
      }
    }
    //Steven starts
    if (table.tableInfo.id === "tokenized_review") {
      for (var key in res_in_json) {
        if (res_in_json.hasOwnProperty(key)) {
          // here you have access to
          var reviewId = res_in_json[key].reviewId;
          //steven starts
          var list_tokenized_words = res_in_json[key].tokenized_words;
          //console.log(list_tokenized_words);
          for (var i = 0; i < list_tokenized_words.length; i++) {
            //console.log("Words-->" + list_tokenized_words[i]);
            var single_word = list_tokenized_words[i];
            tableData.push({
              reviewId: reviewId,
              tokenizedReview: single_word
            });
          }
          //steven ends
        }
      }
    }
    //Steven ends
    //table.appendRows(tableData);
    console.log("Total records (tokenized matters) fetched " + tableData.length);
    var row_index = 0;
    var size = 100;
    while (row_index < tableData.length) {
      table.appendRows(tableData.slice(row_index, size + row_index));
      row_index += size;
      if (row_index % size === 0) {
        tableau.reportProgress("Getting row: " + row_index);
        //console.log("Getting row: " + row_index);
      }
    }
    doneCallback();	
  });
  
};

tableau.registerConnector(myConnector);
window._tableau.triggerInitialization &&
  window._tableau.triggerInitialization(); // Make sure WDC is initialized properly

function submit() {
  let app_name = $("#query").val();
  if (app_name === "") return error("Please enter a valid app name.");
  tableau.connectionData = JSON.stringify({ app_name });
  tableau.connectionName = "GooglePlay Reviews";
  tableau.submit();
}

//draft function to handle for error, yet to use
function error(message) {
  $("#error").html(message);
  $("#submit").prop("disabled", false);
}
