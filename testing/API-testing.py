import requests
import csv, io
import itertools
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://localhost:9876/api"
VERIFY_SSL = False # need it false for self-signed certificates

valid_status = [None,"available","charging","offline","malfunction","reserved"]
valid_formats = [None,"json","csv"]


#Testing functional API's
def test_points():
    BASE_URL=API_URL+"/points"
    print(f"Starting {BASE_URL} testing")
    for fmt in valid_formats:
        for status in valid_status:
            params={}
            URL= BASE_URL
            if status is not None:
                params["status"]=status
            if fmt is not None:
                params["format"]=fmt

            response = requests.get(URL, params=params, verify=VERIFY_SSL)

            assert response.status_code in (200,204) , f"Status {response.status_code} for fmt={fmt}, status={status}\n Body: {response.text[:200]}"

            if response.status_code == 204:
                # Empty result is valid for this filter
                print(f"WARNING: {BASE_URL} is empty for {status}")
                continue

            if fmt=="csv":
                assert "text/csv" in response.headers["Content-Type"], f"Status {response.status_code} for fmt={fmt}, status={status}\n Body: {response.text[:200]}"
                data = list(csv.DictReader(io.StringIO(response.text)))
            else:
                assert "application/json" in response.headers["Content-Type"], f"Status {response.status_code} for fmt={fmt}, status={status}\n Body: {response.text[:200]}"
                data=response.json()
            assert isinstance(data, list)

            #assert len(data)>0 #at least one charger

            if len(data)>0:
                charger=data[0]
                assert "pointid" in charger
                assert "lon" in charger
                assert "lat" in charger
                assert "cap" in charger
                assert "status" in charger

                if status is not None:
                    assert charger["status"]==status, f"Status {response.status_code} for fmt={fmt}, status={status}\n Body: {response.text[:200]}"
    print(f"{BASE_URL} testing ok!")


#old - not used
"""
def _param_combinations(path_params: dict, query_params: dict):
    
    #path_params: {"token": ["abc"]}  (values are lists)
    #query_params:  {"status": [None,"available"], "format":[None,"json","csv"]}
    
    path_params = path_params or {}
    query_params = query_params or {}

    keys = list(path_params.keys()) + list(query_params.keys())
    values_lists = [path_params[k] for k in path_params] + [query_params[k] for k in query_params]

    for combo in itertools.product(*values_lists):
        params = {}
        ctx = {}
        for k, v in zip(keys, combo):
            ctx[k] = v
            if v is not None:
                params[k] = v
        yield params, ctx
"""
def _param_combinations(all_params: dict):
    all_params =all_params or {}

    keys = list(all_params.keys())
    values_lists =[all_params[k] for k in all_params]

    for combo in itertools.product(*values_lists):
        params = {}
        ctx = {}
        for k, v in zip(keys, combo):
            ctx[k] = v
            if v is not None:
                params[k] = v
        yield params, ctx

def _test_get_endpoint_inner(
        endpoint: str,                      #the endpoint we want to check
        #*,                                 #Use to force later arguments to be passed by name, not used as of now
        #path_params: dict | None = None,   #use in wrapper
        query_params: dict | None = None,  #optional parameters if applicable
        verify_ssl: bool = False,             #false to work
        accept_empty_as_204: bool = True,     #in case a field is empty (for example reserved)
        need_valid_answer: bool = True,       #set false to test non 200/204 codes
        return_list: bool = False,            #set true if you return list
        return_types: dict | None = None,    #what do you expect to get?
        check_type: bool = True
):
    print(f"Testing {endpoint} ")
    BASE_URL=API_URL+endpoint
    return_types = return_types or []
    #path_params = path_params or {}
    query_params = query_params or {}
    gen = _param_combinations(query_params) if query_params else [({}, {})]

    for params,ctx in gen:
        URL=BASE_URL

        r = requests.get(URL, params=params, verify=verify_ssl)# r is response

        assert (
            (not need_valid_answer) or r.status_code == 200 or (r.status_code==204 and accept_empty_as_204)
                ),(
                    f"ctx={ctx}, status_code={r.status_code}, body={r.text[:200]}"
                )
        
        if r.status_code!=200:
            print(f"Warning! Status code is {r.status_code} for ctx={ctx}")
            continue

        if "format" in params and params["format"]=="csv":
            assert "text/csv" in r.headers["Content-Type"], f"ctx={ctx}, status_code={r.status_code}, body={r.text[:200]}"
            data = list(csv.DictReader(io.StringIO(r.text)))
        else:
            assert "application/json" in r.headers["Content-Type"],f"ctx={ctx}, status_code={r.status_code}, body={r.text[:200]}"
            data=r.json()

        if return_list:
            assert isinstance(data, list)
            test_subject=data[0]
        else:
            assert isinstance(data, dict)
            test_subject=data

        for field, expected_type in return_types.items():
            assert field in test_subject, f"Missing {field}"
            if check_type:
                assert isinstance(test_subject[field], expected_type), (
                    f"{field} wrong type: got {type(test_subject[field])}, expected {expected_type}"
                )
        
        for param in params:
            if param in return_types:
                assert test_subject[param]==params[param]
        print(f"just tested ctx = {ctx}")

    print(f"Testing {endpoint} finished!")

def test_get_endpoint(
        endpoint: str,                      #the endpoint we want to check
        #*,                                 #Use to force later arguments to be passed by name, not used as of now
        path_params: dict | None = None,   #use in wrapper
        query_params: dict | None = None,  #optional parameters if applicable
        verify_ssl: bool = False,             #false to work
        accept_empty_as_204: bool = True,     #in case a field is empty (for example reserved)
        need_valid_answer: bool = True,       #set false to test non 200/204 codes
        return_list: bool = False,            #set true if you return list
        return_types: dict | None = None,    #what do you expect to get?
        check_type: bool = True
):
    p_gen = _param_combinations(path_params) if path_params else [({}, {})]
    return_types = return_types or {}
    for params,ctx in p_gen:
        true_endpoint=endpoint.format(**params)
        
        _test_get_endpoint_inner(
        endpoint=true_endpoint,
        query_params=query_params,
        verify_ssl=verify_ssl,
        accept_empty_as_204=accept_empty_as_204,
        need_valid_answer=need_valid_answer,
        return_list=return_list,
        return_types=return_types,
        check_type=False
        )



if __name__ == "__main__":
    """
    test_get_endpoint(
        endpoint="/points",
        query_params={"status":valid_status, "format":valid_formats},
        return_list=True,
        return_types={"providerName": str,"pointid": str,"lon":str,"lat":str,"status":str,"cap":int},
        check_type = False
    )
    
    test_get_endpoint(
        endpoint="/point/{point_id}",
        path_params={"point_id":[4,5,6,7,189,"lmao"]},
        need_valid_answer=False,
        #query_params={"format":valid_formats},
        return_types={"pointid":str,"lon":str,"lat":str,"status":str,"cap":int,"reservationendtime":str,"kwhprice":float},
        check_type = False
    )

    test_get_endpoint(
        endpoint="/sessions/{point_id}/{from}/{to}",
        path_params={"point_id":[4,5,6,7,189,"lmao"], "from":["20201020"], "to":["20301020"]},
        need_valid_answer=False,
        query_params={"format":valid_formats},
        return_list=True,
        return_types={"starttime":str,"endtime":str,"startsoc":int,"endsoc":int,"totalkwh":float,"kwhprice":float,"amount":float},
        check_type = False  
    )
    """

    test_get_endpoint(
        endpoint="/pointstatus/{point_id}/{from}/{to}",
        path_params={"point_id":[1224,1309,1010,785,189,"lmao"], "from":["20201020"], "to":["20301020"]},
        need_valid_answer=False,
        query_params={"format":valid_formats},
        return_list=True,
        return_types={"timeref":str,"old_state":str,"new_state":str},
        check_type = False  
    )
