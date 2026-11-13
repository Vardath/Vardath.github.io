-- Galactic Occupations 0.5.3: preserve native transport confirmations.
-- The former v46 observer hooked UserQuestionMenu.confirm for a zone target,
-- which also occurs during ordinary docking/transporter interactions. Its
-- delayed MD recovery could forcibly teleport and eject the player.
-- This legacy module remains for extension/file compatibility but is inert.
local existing = rawget(_G, "VGOSpacesuit")
if existing then return existing end
local S = {}
_G.VGOSpacesuit = S
function S.install() end
RegisterEvent("VGO.Install", S.install)
return S
