"""Student explainers (11–16). English only. School-safe, no gore."""

from __future__ import annotations

STUDENTS: list[tuple] = [
    ("How Does a Circuit Work?", "circuit", "#FFC107", "A bulb is a tiny closed racetrack for charge.", "A battery pushes charge around a complete loop.", "Break the loop and the light dies.", "Series shares one path. Parallel gives each bulb its own."),
    ("What Is an Atom?", "star", "#90CAF9", "An atom is a tiny building block of stuff.", "A nucleus sits in the middle. Electrons cloud around it.", "Different numbers make different elements.", "You are walking chemistry sets."),
    ("What Is Gravity, Really?", "apple", "#E53935", "Gravity is mass attracting mass.", "Newton described the pull. Einstein described warped spacetime.", "Near Earth, the simple pull-down picture still works.", "That is why homework stays on the desk."),
    ("Photosynthesis in One Minute", "leaf", "#66BB6A", "Leaves trap sunlight with chlorophyll.", "Carbon dioxide plus water become sugar and oxygen.", "We breathe the leftover oxygen.", "A forest is a quiet sugar factory."),
    ("States of Matter", "ice", "#4FC3F7", "Solid, liquid, gas: same stuff, different packing.", "Heat jiggles particles until they slip or fly.", "Ice, water, steam are one molecule in three moods.", "Phase change is a costume change, not a new actor."),
    ("Density Without the Headache", "water", "#0277BD", "Density is mass per volume.", "Oil floats on water because it is less dense.", "A steel ship floats by enclosing lots of air.", "Shape plus density beats 'heavy things sink'."),
    ("Friction: Friend and Foe", "car", "#78909C", "Friction is resistance when surfaces rub.", "You walk because friction grips your shoes.", "Too much friction wastes energy as heat.", "Oil, wax, and bearings are friction managers."),
    ("Kinetic vs Potential Energy", "ball", "#FFA726", "Potential is stored. Kinetic is motion.", "A held ball has potential. A falling ball spends it as kinetic.", "Energy changes form. The total in a closed system stays put.", "That bookkeeping is conservation of energy."),
    ("What Is a Cell?", "heart", "#80CBC4", "A cell is the smallest living workshop.", "Membrane on the outside. Machinery inside.", "Plant cells have walls and chloroplasts. Animal cells do not.", "You are about thirty trillion workshops cooperating."),
    ("DNA Is a Recipe, Not a Destiny", "book", "#5C6BC0", "DNA stores instructions in four letters.", "Genes are stretches of that recipe.", "Environment and choices still matter.", "Biology is not a prison sentence."),
    ("Plate Tectonics", "rock", "#6D4C41", "Earth's crust is cracked into slow plates.", "They collide, dive, and slide.", "Mountains, quakes, and volcanoes follow the seams.", "Your continent is a raft on geologic time."),
    ("The Water Cycle", "rain", "#29B6F6", "Evaporate, condense, precipitate, collect.", "The sun is the pump.", "Rivers, clouds, and groundwater are one loop.", "Your glass of water has been through the sky."),
    ("Climate vs Weather", "earth", "#26A69A", "Weather is this week's mood.", "Climate is the decades-long personality.", "One cold day does not cancel a warming climate.", "Think of climate as the uniform. Weather is the play."),
    ("Why Refraction Bends Light", "rainbow", "#29B6F6", "Light changes speed in glass or water.", "The wavefront pivots. The ray looks bent.", "Lenses use this on purpose.", "A straw in a glass looks broken. It is not."),
    ("Sound Is a Wave", "ear", "#FFCCBC", "Sound is a compression wave in matter.", "Faster in steel than in air. Silent in vacuum.", "Pitch is frequency. Loudness is amplitude.", "Your eardrum is a microphone."),
    ("The Periodic Table Logic", "book", "#7E57C2", "Elements are sorted by proton number.", "Columns share similar outer electrons, so similar chemistry.", "Noble gases are already 'done' and rarely react.", "The table is a seating chart for atoms."),
    ("What Is Pressure?", "wave", "#0277BD", "Pressure is force over area.", "A sharp knife cuts because the area is tiny.", "Deep ocean pressure could crush an unready sub.", "Snowshoes work by spreading your force."),
    ("Newton's Three Laws", "rocket", "#FF7043", "Stay still or keep moving unless a net force acts.", "F equals m a. More force or less mass means more acceleration.", "Every push has an equal opposite push.", "A rocket is law three with a fuel tank."),
    ("What Is a Molecule?", "star", "#81D4FA", "A molecule is atoms bonded in a set recipe.", "H2O is two hydrogen plus one oxygen.", "Shape plus ingredients decide the behavior.", "Water's bent shape is why it is so clingy and useful."),
    ("Acids and Bases, Gently", "water", "#AED581", "pH measures how acidic or basic a solution is.", "Lemon is acidic. Soap is basic.", "The scale is logarithmic, so small number shifts are big.", "Never mix random cleaners. Chemistry is not a smoothie."),
    ("What Is Electricity?", "circuit", "#FFC107", "Electricity in wires is a flow of charge.", "Voltage is the push. Current is the flow rate.", "Resistance fights the flow and makes heat.", "Ohm's law ties those three together."),
    ("Magnets and Moving Charge", "magnet", "#E53935", "Moving charge makes magnetism.", "A changing magnetic field can push charge in a wire.", "That is a generator. Reverse it: a motor.", "Your phone charger is this idea in a brick."),
    ("What Is a Wave on the Ocean?", "wave", "#0288D1", "Energy travels. Water mostly goes up and down.", "Wind piles energy into the surface.", "When the wave hits a beach, the bottom drags and it breaks.", "Surf is delivered energy, not a wall of water from far away."),
    ("The Speed of Light", "star", "#3949AB", "Light in vacuum is the universe's speed limit.", "About 300,000 kilometers per second.", "It still takes over a second to bounce off the moon.", "Astronomy is looking at the past."),
    ("Black Holes, Kid-Honest", "star", "#1A237E", "A black hole is a region where gravity wins so hard light cannot climb out.", "They are not cosmic vacuum cleaners eating the solar system.", "We infer them from orbits and glowing disks.", "Stay curious. Stay accurate. No horror movie physics."),
    ("What Is Evolution?", "seed", "#8BC34A", "Populations change over many generations.", "Traits that help survival and reproduction show up more later.", "It is not a ladder with humans at the top.", "It is a branching family tree of life."),
    ("Fossils Are Time Capsules", "rock", "#8D6E63", "A fossil can be bone, imprint, or even a footprint.", "Sediment buries. Minerals sneak in. Rock remembers.", "Index fossils help date layers.", "Museums are libraries of deep time."),
    ("The Carbon Cycle", "earth", "#66BB6A", "Carbon hops from air to plants to animals to soil and back.", "Burning fossil fuels dumps extra carbon into air fast.", "That extra traps heat.", "The cycle was balanced. We pushed the throttle."),
    ("What Is a Vaccine, Precisely?", "heart", "#80CBC4", "A vaccine shows your immune system a safe sample or instruction.", "Memory cells remember the threat.", "Later infection meets a prepared team.", "Herd immunity is neighbors protecting neighbors who cannot vaccinate."),
    ("Antibiotics Are Not for Viruses", "heart", "#EF9A9A", "Antibiotics target bacteria, not viruses.", "Colds are usually viral. The pills will not help.", "Misuse breeds resistant bacteria.", "Finish a prescribed course. Do not share leftovers."),
    ("What Is a Neuron?", "eye", "#CE93D8", "A neuron is a message cell.", "Electrical pulses hop down the axon.", "Chemicals jump the gap to the next cell.", "Thoughts are coordinated storms of these hops."),
    ("The Eye as a Camera", "eye", "#90CAF9", "Cornea and lens focus. Retina senses.", "Rods handle dim. Cones handle color.", "The brain flips and interprets the image.", "Glasses bend light so the focus lands on the retina."),
    ("How Hearing Works", "ear", "#FFCCBC", "Eardrum to tiny bones to coiled inner ear.", "Hair cells turn motion into nerve signals.", "Loud sound can wreck those hair cells for good.", "Hearing loss is often preventable. Volume matters."),
    ("What Is Blood Pressure?", "heart", "#E57373", "It is the push of blood on artery walls.", "Systolic is the squeeze. Diastolic is the rest.", "Too high for too long stresses organs.", "Sleep, salt, and movement all talk to this number."),
    ("Calories Are Energy", "apple", "#FF7043", "A food calorie is a unit of energy.", "Your body spends them on thinking, heat, and motion.", "Not all calorie sources treat you the same.", "Fuel quality still matters, not just the count."),
    ("Sleep Architecture", "moon", "#5C6BC0", "Sleep cycles through light, deep, and REM.", "Deep sleep repairs. REM is rich in dreams and memory glue.", "Phones steal from both.", "A regular bedtime is a performance drug that is free."),
    ("What Is Inflation, Briefly?", "book", "#FFD54F", "Inflation is a general rise in prices.", "The same rupee buys less.", "Causes include too much money chasing too few goods.", "It is why 'my parents' candy was cheaper' is not only nostalgia."),
    ("Supply and Demand", "apple", "#AED581", "More buyers than stuff: prices tend to rise.", "More stuff than buyers: prices tend to fall.", "A drought can shrink supply of grain.", "Markets are arguments made of prices."),
    ("What Is a Vote?", "book", "#5C6BC0", "A vote is a formal say in a shared decision.", "Democracy is messy on purpose so power is not a monopoly.", "Informed votes beat loud votes.", "Civics is a skill, not a vibe."),
    ("How Laws Get Made, Simple", "book", "#6D4C41", "An idea is drafted, debated, voted, signed.", "Details differ by country.", "Laws can be changed. That is a feature.", "Complaining plus learning beats only complaining."),
    ("What Is Bias?", "eye", "#7E57C2", "Bias is a lean in judgment, often unnoticed.", "Everyone has some. Scientists try to trap theirs with methods.", "A diverse team catches more blind spots.", "Curiosity about your own lean is intellectual honesty."),
    ("Correlation Is Not Causation", "book", "#26A69A", "Two things can rise together without one causing the other.", "Ice cream sales and sunburn both rise in summer.", "Heat is the hidden driver.", "Good science hunts the hidden driver."),
    ("What Is Pi?", "shape", "#29B6F6", "Pi is circumference divided by diameter, for any circle.", "It never repeats as a decimal.", "Engineers still use handy approximations.", "A circle's secret ratio, hiding in wheels and orbits."),
    ("Percentages in Real Life", "clock", "#FFA726", "Percent means per hundred.", "A 10 percent off sale on 200 is 20 off.", "Interest rates are percents with time attached.", "This is money-and-marks literacy."),
    ("Mean, Median, Mode", "book", "#90CAF9", "Mean is the average. Median is the middle. Mode is the most common.", "A huge outlier yanks the mean.", "Median can tell a fairer typical story.", "Choose the stat that matches the question."),
    ("What Is an Algorithm?", "circuit", "#00ACC1", "An algorithm is a finite recipe of steps.", "Search, sort, recommend: algorithms behind the screen.", "Biased data in, biased results out.", "You can audit a recipe. Demand that adults do."),
    ("Binary in One Minute", "circuit", "#26C6DA", "Binary uses two digits, 0 and 1.", "Place values double: 1, 2, 4, 8.", "Thirteen is 1101.", "Computers love two states because switches are cheap."),
    ("What Is the Internet?", "circuit", "#5C6BC0", "A network of networks agreeing on how to pass packets.", "Your photo is sliced, addressed, and rebuilt.", "No single owner. Many pipes.", "The cloud is just someone else's computer."),
    ("Encryption, Plainly", "lock", "#455A64", "Encryption scrambles data with a key.", "HTTPS is that scramble in your browser.", "Without the key, the message looks like noise.", "That is why cafe wifi is less scary than it used to be. Still, do not bank on sketchy pages."),
    ("History of Writing", "book", "#8D6E63", "Marks on clay, then ink, then print, then pixels.", "Writing froze speech so empires and science could scale.", "Literacy used to be rare. Now it is a right to fight for.", "You are using a 5,000-year-old superpower."),
    ("The Scientific Method", "star", "#FFC107", "Question, hypothesize, test, check, share, repeat.", "A result nobody can repeat is a rumor in a lab coat.", "Peer review is organized skepticism.", "Changing your mind with evidence is a flex."),
    ("What Is a Hypothesis?", "book", "#81D4FA", "A hypothesis is a testable guess.", "If-then. Measurable. Willing to die if the data say no.", "It is not a vibe and not a proof.", "Kill your bad guesses early. That is the job."),
]


def pack_students() -> list[dict]:
    out = []
    for row in STUDENTS:
        title, scene, accent, *lines = row
        out.append(
            {
                "title": title,
                "scene": scene,
                "accent": accent,
                "hook": lines[0],
                "narration": list(lines),
            }
        )
    return out
