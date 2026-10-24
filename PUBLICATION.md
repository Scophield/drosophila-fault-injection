# Fixed V10 publication identities

Scientific baseline:43bcd4d6a99b2d9b258cf8a198a4545d237b5c39 (full V9 research).
Frozen V10 code/data:986ff54193fee6a1b95815499a4a3477b15ea49a.

This later enclosing Git commit binds the final manuscript and updated public
reproduction entry to the same experimental records and scientific code. Use
its complete SHA (git rev-parse HEAD), not the earlier candidate PDF, as the
final-paper identifier. The paper cites the earlier fixed code/data snapshot;
a PDF cannot embed its own enclosing commit hash. PUBLIC_SCOPE.json binds file
bytes without self-hashing that manifest. Original generation HEADs, snapshots,
registrations, maps, calibrations and observations remain unaltered.

Final four-figure main PDF SHA256:
295b07b85ff152bfe17d59612edff9bec3124a9e3380a3db79b535d87ab16ebe.
The same bytes are stored at paper/main.pdf and
paper/fly_connectome_fault_assessment_v10_final.pdf. Source is
paper/main_v10_final4.tex with sections/v10f_*.tex and refs.bib.

No GitHub Release, conference submission or main/V9 update. No forbidden SI
attachment, unresolved-license source tables, private Blender projects or
caches are distributed. See README.md, PUBLIC_SCOPE.json, THIRD_PARTY_LICENSES
and audit/v10-final/public-checks.json. Public code/data saved-record checks
actually ran in a new anonymous checkout on the SAME host, with existing minimal
packages; this is not a neural rerun or second-host replication.
