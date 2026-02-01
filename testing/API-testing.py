import requests
import csv, io
import itertools
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://localhost:9876/api"
VERIFY_SSL = False # need it false for self-signed certificates

valid_status = [None,"available","charging","offline","malfunction","reserved"]
formats = [None,"json","csv"]


#Testing functional API's
def test_points():
    BASE_URL=API_URL+"/points"
    print(f"Starting {BASE_URL} testing")
    for fmt in formats:
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
            

def _param_combinations(mandatory_params: dict, optional_params: dict):
    """
    mandatory_params: {"token": ["abc"]}  (values are lists)
    optional_params:  {"status": [None,"available"], "format":[None,"json","csv"]}
    """
    mandatory_params = mandatory_params or {}
    optional_params = optional_params or {}

    keys = list(mandatory_params.keys()) + list(optional_params.keys())
    values_lists = [mandatory_params[k] for k in mandatory_params] + [optional_params[k] for k in optional_params]

    for combo in itertools.product(*values_lists):
        params = {}
        ctx = {}
        for k, v in zip(keys, combo):
            ctx[k] = v
            if v is not None:
                params[k] = v
        yield params, ctx


def test_get_endpoint(
        endpoint: str,
        *,
        mandatory_params: dict | None = None,
        optional_params: dict | None = None,
        verify_ssl: bool = False,
        accept_empty_as_204: bool = True,
        need_valid_answer: bool = True,
        return_list: bool = False,
        return_fields: list | None = None,
):
    print(f"Testing {endpoint} ")
    BASE_URL=API_URL+endpoint
    gen=_param_combinations(mandatory_params, optional_params)
    return_info = return_info or []
    mandatory_params = mandatory_params or {}
    optional_params = optional_params or {}

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

        for field in return_fields:
            assert field in subject

    print(f"Testing {endpoint} finished!")

if __name__ == "__main__":
