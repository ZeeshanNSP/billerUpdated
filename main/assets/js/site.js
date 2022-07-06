


const SERVER_IP = "10.39.13.199";

const GENERATE_API = () => {
    let now = new Date().toLocaleDateString('en-us', { year: 'numeric', weekday: "short", month: "short" });
    now = now.split(" ")
    year = now[1]
    mon = now[0]
    day = now[2]
    now = `${year}${mon}${day}chaman`
    var hash = CryptoJS.MD5(now);
    hash = hash.toString().substr(0, 12)
    return hash
}
const GetSortOrder = (prop) => {
    return function (a, b) {
        if (a[prop] > b[prop]) {
            return 1;
        } else if (a[prop] < b[prop]) {
            return -1;
        }
        return 0;
    }
}  
const isIn = (key, arr) => {
    for (i in arr) {
        if (key == arr[i]) {
            return true;
        }
    }
    return false
}
const getDates = (differ = 30) => {
    const date = new Date();
    let year = date.getFullYear()
    let month = date.getMonth()+1
    let day = date.getDate()
    if (month < 10) {
        month = `0${month}`;
    }
    if (day < 10) {
        day =`0${day}`
    }
    let from_date = `${year}-${month}-${day}`
    date.setDate(date.getDate() + differ);
     year = date.getFullYear()
     month = date.getMonth()+1
     day = date.getDate()
    if (month < 10) {
        month = `0${month}`;
    }
    if (day < 10) {
        day = `0${day}`
    }
    let to_date = `${year}-${month}-${day}`

    return { "from": from_date, "to": to_date }

}
const SITE = (site_name,site_init) => {
    return {
        "name": site_name,
        "initial":site_init
    }
}
const SITE_DATA = {
    "264": SITE("JWP-SH 130","JWPSH130"),
    "262": SITE("4401","4401"),
    "499": SITE("Concord 1","CC01"),
    "422": SITE("Danube","DB"),
    "263": SITE("JFM 3","JFM03"),
    "272": SITE("JWP 100","JWP100"),
    "318": SITE("JWP 150","JWP150"),
    "273": SITE("JWP 190","JWP190"),
    "331": SITE("JWP 204","JWP204"),
    "283": SITE("JWP 272","JWP272"),
    "265": SITE("JWP SH-1","SH01"),
    "266": SITE("JWP-130","JWP130"),
    "432": SITE("JWP-Z115","JWPZ115"),
    "396": SITE("JWP-Z25","JWPZ25"),
    "419": SITE("Lootah 3","LT03"),
    "420": SITE("Mega 1","M1"),
    "258": SITE("Omma","OM"),
    "329": SITE("Serhub2","SH02"),
    "504": SITE("Zajel 118","ZJ118"),
    "338": SITE("Zajel 78","ZJ78")
}

const POPUP_DELAY = 2000;
const PAGE_FORWARD_LONG_DELAY = 5000;
const WEATHER_URL_END_POINT = "https://api.openweathermap.org/data/2.5/weather?q=Dubai,uae&APPID=61b6a820be1ee9f1976641ed8f99f62b&units=metric";
const CASH_TIME_OUT = 15000;
const API_KEY = GENERATE_API()
const SITE_ID = "329"
const DATES = getDates() 
const ALLOWED_SERVICES = ["jwp"]
const GET_PROFILES_END_POINT = `https://protik.ae/jwp_api_official/home/get_profiles/${SITE_ID}/${API_KEY}`;
const GET_USER_END_POINT = `https://protik.ae/jwp_api_official/home/search_user/${API_KEY}?term=`;
const GET_SITE_ACTIVATIONS_END_POINT = `http://protik.ae/jwp_api_official/home/activations/${SITE_ID}/${API_KEY}/${DATES["from"]}/${DATES["to"]}`
const VOUCHER_GENERATE_END_POINT = `https://protik.ae/jwp_api_official/home/live_sale/${SITE_ID}/${API_KEY}/`
const ADD_PENDING_AMOUNT_END_POINT = `https://protik.ae/jwp_api_dev/home/add_pending_amount/${SITE_ID}/${API_KEY}/`;
$(document).ready(() => {

   
    $.get(WEATHER_URL_END_POINT, function (data) {
        let stat = data["weather"]["main"]
        let temp = data["main"]["temp"]
        $("#temp").text(temp)
        if (stat == "Clear") {
            $("#weather-img").attr("src", "./assets/sunny.png");
        }
    });
    var pleaseWait = $('#pleaseWaitDialog');
    
    showPleaseWait = function () {
        pleaseWait.modal('show');
    };

    hidePleaseWait = function () {
        pleaseWait.modal('hide');
    };


    $(".back-button").on("click", (e) => {
        history.back();
    });
    $(".next-button").on("click", (e) => {
        let pageId = $("title").text().split("-")[0].trim().toLowerCase();


        console.info(`[PAGE ID] ${pageId}`)
        if (pageId == "details") {
            let num = $(".input").val();
            if (num.length < 12) {
                alertify.alert("<h1 class='text-danger'>Incorrect Number</h1>").set({ title: "Warning" }).set('closable', false).show();
            }
            else {
                let previous_json = JSON.parse(localStorage.getItem("obj"));
                previous_json['number'] = num.replaceAll("-", "");
                localStorage.setItem("obj",JSON.stringify(previous_json))
                window.location.href = "/cash-acceptor"
            }
        }
        if (pageId == "cash") {

            let amount = parseFloat($("#balance").text())
            console.log(amount)
            if (amount > 0) {
                showPleaseWait();
             
                let previous_json = JSON.parse(localStorage.getItem("obj"))
                previous_json['amount'] = amount;
                localStorage.setItem("obj", JSON.stringify(previous_json));
                //  setTimeout(hidePleaseWait, POPUP_DELAY);
                setTimeout(() => {
                    window.location.href = "/final";
                }, PAGE_FORWARD_LONG_DELAY)
            }
            else {
                alertify.alert("<h1 class='text-danger'>An Error Occured</h1>").set({ title: "Error" }).set('closable', false).show();
            }
        }
        if (pageId == "jwp") {
            let num = $(".input").val();
            num = num.replaceAll("-", "");
            num = num.substr(1, 10);
            num = `971${num}`
            showPleaseWait()
            $.get(`${GET_USER_END_POINT}${num}`, function (data) {
                d = JSON.parse(data);
                hidePleaseWait()
                if (d.length > 0) {
                    person = d[0]
                    let previous_json = JSON.parse(localStorage.getItem("obj"))
                    if (previous_json == null || previous_json == undefined) {
                        previous_json = {}
                    }
                    previous_json["company"] = "JWP";
                    previous_json["number"] = num;
                    previous_json["person"] = person
                    localStorage.setItem("obj", JSON.stringify(previous_json))

            window.location.href= "/plan"
                }
                else {
                    alertify.alert("<h1 class='text-danger'>Incorrect Mobile Number</h1>").set({ title: "Error" }).set('closable', false).set('onok', function (closeEvent) { window.location.reload(); }).show();
                      
                }

            })
          

        
        }
        if (pageId == "cashjwp") {
            let previous_json = JSON.parse(localStorage.getItem('obj'))
            //Amar Blouch / 971521149088 / 5 - Days
            let customer_name = previous_json['person']['name']
            let customer_mobile = previous_json['person']['mobile']
            let customer_profile = previous_json['plan']['profile']

            $.get(`${VOUCHER_GENERATE_END_POINT}${customer_name}/${customer_mobile}/${customer_profile}`, (data) => {
                data = JSON.parse(data)
                if (data['type'] == "success") {
                    previous_json['voucher'] = data['code']
                    localStorage.setItem("obj", JSON.stringify(previous_json))
                    let post_data = {
                        "code": data["code"],
                        "profile": previous_json["plan"]["profile"],
                        "phone": previous_json["number"],
                        "site": SITE_DATA[SITE_ID]["initial"],
                        "amount":previous_json["plan"]["price"]
                    }
                    $.post(`https://${SERVER_IP}:443/voucherPrint`, post_data, (d) => {
                        
window.location.href="/final"
                    })
                }
                
            })
           
        }
        
       
    });
})