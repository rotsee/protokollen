Database API
============

The [Protokollen site](http://www.protokollen.net) uses an API to query the Elasticsearch database. This is endpoint is open to GET and POST requests.

You can pass JSON objects to the endpoint to make [Elasticsearch queries](https://www.elastic.co/guide/en/elasticsearch/reference/current/search.html). This query 

__Request URI:__ `https://protokollen.herokuapp.com/api/documents/_search?size=10&from=0&fields=origin,meeting_date,document_type,text_file,file,text,last_updated,source`

__Content-Type:__ `application/json`

__Request payload:__

``` javascript
{
    "filter": {
        "bool": {
            "must": [
                {
                    "terms": {
                        "document_type": [
                            "kommunstyrelseprotokoll"
                        ]
                    }
                },
                {
                    "terms": {
                        "origin": [
                            "Arvidsjaurs kommun"
                        ]
                    }
                }
            ]
        }
    },
    "sort": [
        {
            "meeting_date": {
                "order": "desc"
            }
        }
    ]
}
```