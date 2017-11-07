print "Copying files for Kerbin Orbit and Return".
declare parameter orbAlt.

copypath("0:/launch","").
copypath("0:/donode","").
copypath("0:/warpTo","").
copypath("0:/commsDeploy","").

run launch(orbAlt).

wait 5.

clearscreen.
print "................................................".
print "StreffX Cosmic Tourism team welcomes you to space.".
print "................................................".

set gooList to ship:PARTSNAMED("GooExperiment").
set jrList to ship:PARTSNAMED("science.module").
set thermList to ship:PARTSNAMED("sensorThermometer").

print "comms on".
run commsDeploy.
print "Getting science".
if gooList:length > 0 {
SET P TO gooList[0].
SET M TO P:GETMODULE("ModuleScienceExperiment").
M:DEPLOY.
WAIT UNTIL M:HASDATA.
}.

if jrList:length > 0 {
SET P1 TO jrList[0].
SET M1 TO P1:GETMODULE("ModuleScienceExperiment").
M1:DEPLOY.
WAIT UNTIL M1:HASDATA.
}.


if thermList:length > 0 {
SET P3 TO thermList[0].
SET M3 TO P3:GETMODULE("ModuleScienceExperiment").
M3:DEPLOY.
WAIT UNTIL M3:HASDATA.
}.
lights off.
clearscreen.
print "Awaiting EVA.".
wait until Lights.

wait 5.

print "Pointing nose Retrograde...".
lock steering to retrograde.

print "Burn for DeOrbit.".

wait 5.

lock throttle to 0.5.

wait until periapsis < 25000.

lock throttle to 0.
wait 2.
print "deOrbit set".
wait 2.

print "Ditching remaining tanks....".
wait 2.
stage.
lock steering to retrograde.
print "descending.".
SET chuteList TO LIST().
LIST PARTS IN partList.
FOR item IN partList {LOCAL moduleList TO item:MODULES. FOR module IN moduleList {IF module = "ModuleParachute" {chuteList:ADD(item).}.}.}.

set chuteNum to chuteList:length.
set chutesDeployed to 0.
until ship:altitude < 100 or chutesDeployed > (chuteNum - 1) {
if ship:altitude < 10000 and chutesDeployed < chuteNum {
        FOR chute IN chuteList {
            IF chute:GETMODULE("ModuleParachute"):HASEVENT("Deploy Chute") {
                IF chute:GETMODULE("ModuleParachute"):GETFIELD("Safe To Deploy?") = "Safe" {
                    //chute:GETMODULE("ModuleParachute"):DOACTION("Deploy", TRUE).
					stage.
                    HUDTEXT("Safe to deploy; Arming parachute", 3, 2, 30, YELLOW, FALSE).
					set chutesDeployed to chutesDeployed + 1.
                }.
            }.
        }.
}.wait 1.
}.
		
//end program