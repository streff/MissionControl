declare parameter degFromKSC.

copypath("0:/launch","").
copypath("0:/streff_obt_hohmann","").
copypath("0:/donode","").
copypath("0:/warpTo","").
copypath("0:/intercept","").
copypath("0:/set_inc_lan","").
copypath("0:/circ_ap","").

set pad to latlng(latitude, longitude).

run set_inc_lan.

run launch(100000).

wait 5.

run circ_ap.

//fairings
toggle abort.
wait 4.
panels on.

set clan to ship:obt:lan.
set_inc_lan(0,clan).

wait 2.
run circ_ap.
wait 2.
run streff_obt_hohmann(pad:lng + degFromKSC).
wait 2.
run circ_ap.
set commslist16 to ship:partsdubbed("Communotron 16").
set commslist32 to ship:partsdubbed("Communotron 32").
print "Attempting Short range connection...".

if commslist16:length > 0 {

for comm in commslist16{
comm:GETMODULE("ModuleRTAntenna"):DOEVENT("activate").
}.
}.

if commslist32:length > 0 {

for comm in commslist32{
comm:GETMODULE("ModuleRTAntenna"):DOEVENT("activate").
}.
}.

set commslistDTS to ship:partsdubbed("Comms DTS-M1").
print "Attempting Mid range connection...".

if commslistDTS:length > 0 {
commslistDTS[0]:GETMODULE("ModuleRTAntenna"):DOEVENT("activate").
commslistDTS[0]:GETMODULE("ModuleRTAntenna"):SETFIELD("target","mission-control").
}.