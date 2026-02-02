import requests
import csv, io
import itertools
import urllib3
import os
import sys
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
        check_type: bool = True,
        verify_database: bool = False
):
    print(f"Testing {endpoint} ")
    BASE_URL=API_URL+endpoint
    return_types = return_types or []
    #path_params = path_params or {}
    query_params = query_params or {}
    gen = _param_combinations(query_params) if query_params else [({}, {})]

    for params,ctx in gen:
        

        r = requests.get(BASE_URL, params=params, verify=verify_ssl)# r is response

        invalid_format = (
            "format" in params and params["format"] not in valid_formats
        )
        invalid_status = (
            "status" in params and params["status"] not in valid_status
        )

        if invalid_format or invalid_status:
            assert r.status_code in (400, 422), (
                f"ctx={ctx}, invalid params={ {k: params[k] for k in params if k in ('format','status')} }, "
                f"status_code={r.status_code}, body={r.text[:200]}"
            )
            print(f"just tested invalid ctx = {ctx}")
            continue

        assert (
            (not need_valid_answer) or r.status_code == 200 or (r.status_code==204 and accept_empty_as_204)
                ),(
                    f"ctx={ctx}, status_code={r.status_code}, body={r.text[:200]}"
                )
        
        
        if r.status_code!=200:
            print(f"Warning! Status code is {r.status_code} for ctx={ctx}")
            continue

        if "format" in params and params["format"]=="csv":
            assert "text/csv" in r.headers["Content-Type"], f"ctx={ctx}, status_code={r.status_code}, body={r.text}"
            data = list(csv.DictReader(io.StringIO(r.text)))
        else:
            assert "application/json" in r.headers["Content-Type"],f"ctx={ctx}, status_code={r.status_code}, body={r.text}"
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

        #if verify_database:    #to be added later or deleted
        #    database_check_post()

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
        check_type: bool = False,           #Would be flipped in a real system
        verify_database: bool = False
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
        check_type=check_type,
        verify_database=verify_database
        )



def _test_post_endpoint_inner(
    endpoint:str,
    need_valid_answer: bool = False,
    payloads: list | None = None, #send a list of DICTS as payload to easily call many payloads at once
    using_files: bool = False, #If True, turns payloads from a list of dicts to a list of files
    verify_ssl: bool = False,
    expected_answer_type: dict | None = None,
    check_type: bool = False,              #Check type of return values
    check_error_logs: bool=False,          #Enable checking error logs
    expected_error_logs: dict | None=None, #A dict of DICTS in the format {status_code:{field1:type, field2:type}}
    check_error_type: bool = False,        #check types of error log field
    verify_database: bool = False
):
    BASE_URL=API_URL+endpoint
    payloads = payloads or []
    expected_answer_type = expected_answer_type or {}
    expected_error_logs = expected_error_logs or {}
    print(f"Testing {endpoint} ")
    for payload in payloads:
        if using_files:
            with open(payload, "rb") as f:
                files = {"file": (payload, f, "text/csv")}
                r = requests.post(BASE_URL, files=files, verify=verify_ssl)
        else:
            r=requests.post(BASE_URL, json=payload,verify=verify_ssl)
        print(r.status_code)

        assert r.status_code in (200,201) or not need_valid_answer, f"Expected valid answer, failed with payload={payload}, status_code={r.status_code}, body={r.text}"

        if r.status_code == 204:
            print(f"Warning! Status code 204!")

        if r.status_code in (200,201) :
            if expected_answer_type !={}:
                data=r.json()
                assert isinstance(data,dict)
                test_subject = data
                print(test_subject)
                for field,expected_type in expected_answer_type.items():
                    assert field in test_subject, f"Missing {field}"
                    if check_type:
                        assert isinstance(test_subject[field], expected_type), (
                            f"{field} wrong type: got {type(test_subject[field])}, expected {expected_type}"
                        )
        else:   
            print(f"Warning! Payload {payload} returns status code {r.status_code}!")  
            if check_error_logs:    #check logs with as much depth as required
                try:
                    errorlog = r.json()
                except ValueError:
                    if r.status_code in expected_error_logs:
                        assert False, f"Error code {r.status_code} does not return an errorlog"
                    else:
                        print(f"Warning! Non-JSON error body for statuscode {r.status_code} with payload = {payload}")
                        continue

                if r.status_code in expected_error_logs:    
                    assert isinstance(errorlog,dict), f"errorlog either doesnt exist or is not json for statuscode {r.status_code} with payload = {payload}"
                    print(f"errorlog:{errorlog}") #REMOVE
                    for field,ftype in expected_error_logs[r.status_code].items():
                        assert field in errorlog, f"Missing {field}"
                        if check_error_type:
                            assert isinstance(errorlog[field], ftype), (
                                f"{field} wrong type: got {type(errorlog[field])}, expected {ftype}"
                            )
                else:
                    print(f"Warning! Error code {r.status_code} has an errorlog but has not been inputed to be checked")
        
        #if verify_database:    #to be added later or deleted
        #    database_check_post()

    print(f"Testing {endpoint} finished!")

def test_post_endpoint(
        endpoint: str,                      # the endpoint we want to check
        path_params: dict | None = None,    # use in wrapper (format into endpoint)
        need_valid_answer: bool = False,
        payloads: list | None = None,       # list of DICTS to POST
        using_files: bool = False,          #If True, turns payloads from a list of dicts to a list of files
        verify_ssl: bool = False,
        expected_answer_type: dict | None = None,
        check_type: bool = False,
        check_error_logs: bool = False,
        expected_error_logs: dict | None = None,
        check_error_type: bool = False,
        verify_database: bool = False
):
    p_gen = _param_combinations(path_params) if path_params else [({}, {})]

    for params, ctx in p_gen:
        true_endpoint = endpoint.format(**params)

        _test_post_endpoint_inner(
            endpoint=true_endpoint,
            need_valid_answer=need_valid_answer,
            payloads=payloads,
            using_files=using_files,
            verify_ssl=verify_ssl,
            expected_answer_type=expected_answer_type,
            check_type=check_type,
            check_error_logs=check_error_logs,
            expected_error_logs=expected_error_logs,
            check_error_type=check_error_type,
            verify_database=verify_database,
        )


if __name__ == "__main__":
    
    if not os.path.exists(".USE_TEST_DB"):
        print("NOT CONNECTED TO TESTING DATABASE - SEE /testing/README.txt")
        sys.exit(1)

    test_get_endpoint(
        endpoint="/points",
        query_params={"status":["offline","lmao"], "format":["csv","fakeformat"]},
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


    test_get_endpoint(
        endpoint="/pointstatus/{point_id}/{from}/{to}",
        path_params={"point_id":[1224,1309,1010,785,189,"lmao"], "from":["20201020"], "to":["20301020"]},
        need_valid_answer=False,
        query_params={"format":valid_formats},
        return_list=True,
        return_types={"timeref":str,"old_state":str,"new_state":str},
        check_type = False  
    )

    test_get_endpoint(
        endpoint="/admin/healthcheck",
        return_types={"status":str,"dbconnection":str,"n_charge_points":int,"n_charge_points_online":int,"n_charge_points_offline":int},
        accept_empty_as_204= False,
        check_type = False
    )


    test_post_endpoint(
        endpoint="/updpoint/{id}",
        path_params={"id":[20]},
        payloads=[{"status":"available","kwhprice":0.40},{"status":"LOL","kwhprice":0.40},{"status":"available","kwhprice":"LOL"}],
        expected_answer_type = {"pointid": int, "status": str, "kwhprice": (float, type(None))},
        check_error_logs= True,
        expected_error_logs={400:{},422:{}}
    )

    #this is for /newsession
    BASE={"pointid":1,"starttime":"2026-02-02 10:00","endtime":"2026-02-02 11:00","startsoc":20,"endsoc":80,"totalkwh":20.0,"kwhprice":0.40,"amount":8.0}
    payloads=[BASE]#,{**BASE,"pointid":999999},{**BASE,"starttime":"bad-date"},{**BASE,"endtime":"2026-02-02 09:00"},{**BASE,"startsoc":-1},{**BASE,"startsoc":150},{**BASE,"endsoc":-5},{**BASE,"endsoc":10},{**BASE,"totalkwh":0},{**BASE,"kwhprice":0},{**BASE,"amount":0},{**BASE,"amount":999},{**BASE,"starttime":"2026-02-02 03:00","endtime":"2026-02-02 04:00"}]

    test_post_endpoint(
        endpoint="/newsession",
        payloads=payloads,
        check_error_logs= True,
        expected_error_logs={400:{},422:{}}
    )

    test_post_endpoint( #NEEDS TO BE FIXED
        endpoint="/reserve/{id}/{minutes}",
        path_params={"id":[20],"minutes":[30,40,10000]},
        payloads=[{}],
        expected_answer_type = {"pointid": int, "status": str, "reservationendtime": str},
        check_error_logs= True,
        expected_error_logs={400:{},422:{}}
    )

    test_post_endpoint(
        endpoint="/admin/addpoints",
        payloads=["./newpoints.csv"],
        using_files=True,
        need_valid_answer=True,
        expected_answer_type={"status": str},
        check_type=True,
        check_error_logs=True,
        expected_error_logs={
            400: {"call": str, "timeref": str, "originator": str, "return_code": int, "error": str, "debuginfo": str},
            500: {"call": str, "timeref": str, "originator": str, "return_code": int, "error": str, "debuginfo": str},
        },
        check_error_type=True
    )

    test_post_endpoint(
        endpoint="/admin/resetpoints",
        payloads=[{}],
        need_valid_answer=True,
        expected_answer_type={},
        check_type=False,
        check_error_logs=True,
        expected_error_logs={
            400: {"call": str, "timeref": str, "originator": str, "return_code": int, "error": str, "debuginfo": str},
            500: {"call": str, "timeref": str, "originator": str, "return_code": int, "error": str, "debuginfo": str},
        },
        check_error_type=True
    )
    



