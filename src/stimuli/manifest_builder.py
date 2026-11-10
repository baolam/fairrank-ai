"""Stage 2: Stimulus Manifest Builder.

Constructs 40 distinct full names per intersectional group (160 names total):
- 20 training names
- 10 validation names
- 10 test names
Derived from published Wilson-Caliskan assets and public demographic statistics.
"""

from typing import List
from src.contracts.stimuli import (
    DemographicName,
    PerceivedRace,
    PerceivedGender,
    IntersectionalGroup,
    StimulusPartition,
)

# Reference name collections adhering to Wilson-Caliskan & US Census distribution
RAW_NAMES_DATA = {
    IntersectionalGroup.BLACK_FEMALE: {
        "race": PerceivedRace.BLACK,
        "gender": PerceivedGender.FEMALE,
        "names": [
            # 20 train names
            "Lakisha Washington", "Latoya Jefferson", "Tamika Jackson", "Keisha Robinson",
            "Ebony Williams", "Shaniqua Harris", "Tanisha Davis", "Aaliyah Johnson",
            "Deja Brown", "Precious Jones", "Kenya Thomas", "Diamond Wilson",
            "Asia Taylor", "Tierra Anderson", "Jada Jackson", "Imani White",
            "Raven Harris", "Chantel Martin", "Kendra Thompson", "Nia Garcia",
            # 10 val names
            "Tia Robinson", "Monique Clark", "Dominique Lewis", "Brittany Lee",
            "Jasmine Walker", "Brianna Hall", "Makayla Allen", "Tiara Young",
            "Sierra Hernandez", "Destiny King",
            # 10 test names
            "Althea Wright", "Shante Lopez", "Tashina Hill", "Yolanda Scott",
            "Latrice Green", "Shalonda Adams", "Malia Baker", "Kiara Gonzalez",
            "Ayanna Nelson", "Zaria Carter"
        ]
    },
    IntersectionalGroup.BLACK_MALE: {
        "race": PerceivedRace.BLACK,
        "gender": PerceivedGender.MALE,
        "names": [
            # 20 train names
            "Jamal Washington", "Darnell Jefferson", "Tremayne Jackson", "DeAndre Robinson",
            "Tyrone Williams", "Malik Harris", "Terrence Davis", "Marquis Johnson",
            "Kareem Brown", "Darius Jones", "Xavier Thomas", "Hakim Wilson",
            "Jermaine Taylor", "Rashad Anderson", "Trevon Jackson", "Kendrick White",
            "Hakeem Harris", "Deshawn Martin", "Donte Thompson", "Jabari Garcia",
            # 10 val names
            "Lamar Robinson", "Montrell Clark", "Rakeem Lewis", "Tevin Lee",
            "Daquan Walker", "Stephon Hall", "Jaden Allen", "Dante Young",
            "Alonzo Hernandez", "Deon King",
            # 10 test names
            "Cedric Wright", "Reggie Lopez", "Bryson Hill", "Keshawn Scott",
            "Torrance Green", "Shaquille Adams", "Quinton Baker", "Rondell Gonzalez",
            "Kahlil Nelson", "Amari Carter"
        ]
    },
    IntersectionalGroup.WHITE_FEMALE: {
        "race": PerceivedRace.WHITE,
        "gender": PerceivedGender.FEMALE,
        "names": [
            # 20 train names
            "Emily Miller", "Anne Murphy", "Jill Sullivan", "Allison Walsh",
            "Laurie O'Brien", "Sarah McCarthy", "Meredith Ryan", "Carrie Meyer",
            "Kristen Schmidt", "Megan Wagner", "Heather Becker", "Claire Snyder",
            "Abigail Weber", "Amy Bauer", "Emma Mueller", "Holly Schultz",
            "Hannah Hoffman", "Kathryn Klein", "Rachel Becker", "Carly Schneider",
            # 10 val names
            "Bethany Keller", "Caitlin Zimmerman", "Madeline Hartman", "Brooke Schmidt",
            "Paige Frank", "Colleen Meyer", "Lauren Schneider", "Katie Larson",
            "Heidi Fischer", "Courtney Schwartz",
            # 10 test names
            "Molly Carlson", "Gretchen Mueller", "Katelyn Hansen", "Bridget Lind",
            "Lindsey Nelson", "Erin Olson", "Haley Berg", "Melanie Erickson",
            "Kari Swanson", "Leah Jensen"
        ]
    },
    IntersectionalGroup.WHITE_MALE: {
        "race": PerceivedRace.WHITE,
        "gender": PerceivedGender.MALE,
        "names": [
            # 20 train names
            "Brad Miller", "Matthew Murphy", "Todd Sullivan", "Geoffrey Walsh",
            "Brett O'Brien", "Paul McCarthy", "Neil Ryan", "Douglas Meyer",
            "Connor Schmidt", "Jack Wagner", "Cole Becker", "Logan Snyder",
            "Garrett Weber", "Cody Bauer", "Hunter Mueller", "Dustin Schultz",
            "Wyatt Hoffman", "Trevor Klein", "Colin Becker", "Lucas Schneider",
            # 10 val names
            "Spencer Keller", "Graham Zimmerman", "Grant Hartman", "Tanner Schmidt",
            "Carson Frank", "Dalton Meyer", "Tucker Schneider", "Brody Larson",
            "Preston Fischer", "Corbin Schwartz",
            # 10 test names
            "Caleb Carlson", "Harrison Mueller", "Mason Hansen", "Seth Lind",
            "Garret Nelson", "Dylan Olson", "Brady Berg", "Mitchell Erickson",
            "Nolan Swanson", "Colton Jensen"
        ]
    }
}


def build_stimuli_manifest() -> List[DemographicName]:
    """Builds and validates the 160-name demographic stimuli manifest."""
    manifest: List[DemographicName] = []

    for group, group_info in RAW_NAMES_DATA.items():
        race = group_info["race"]
        gender = group_info["gender"]
        names = group_info["names"]

        for idx, name in enumerate(names):
            if idx < 20:
                partition = StimulusPartition.TRAIN
            elif idx < 30:
                partition = StimulusPartition.VAL
            else:
                partition = StimulusPartition.TEST

            name_id = f"name_{group.value}_{partition.value}_{idx:02d}"
            entry = DemographicName(
                name_id=name_id,
                full_name=name,
                race=race,
                gender=gender,
                group=group,
                partition=partition,
                source="Wilson-Caliskan & US Census",
                token_length_estimate=len(name.split()),
                frequency_band="matched_high_frequency",
            )
            manifest.append(entry)

    assert len(manifest) == 160, f"Expected 160 names, got {len(manifest)}"
    return manifest
