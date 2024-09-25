# Room parser

Technically we just parse vestide every N times throughout the day I guess

https://rooms.vestide.nl/en/


url: https://rooms.vestide.nl 

API: 

GET
/api/accommodation/getlivingspaces/?Skip=0&Take=999

GET
/api/inschrijvingen/getaddress/
data-input=
{
    "postalcode":"FormModel.PostalCode",
    "housenumber":"FormModel.HouseNumber"
}

data-output=
{
    "city":"FormModel.City",
    "streetName":"FormModel.Address"
} 


/api/inschrijvingen/getaddress/?&quot;


<span data-module="data/ApiValue" data-endpoint="/api/inschrijvingen/getaddress" data-input="{&quot;postalcode&quot;:&quot;FormModel.PostalCode&quot;,&quot;housenumber&quot;:&quot;FormModel.HouseNumber&quot;}" data-output="{&quot;city&quot;:&quot;FormModel.City&quot;,&quot;streetName&quot;:&quot;FormModel.Address&quot;}" aria-hidden="false" data-initialized=""></span>
