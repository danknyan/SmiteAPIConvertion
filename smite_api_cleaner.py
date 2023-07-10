#this is the file that contains all of the functions to clean the Smite API information
#global list of delimiters for scalers

#import dependencies
import re
from inspect import currentframe, getframeinfo
import warnings


scalers = [" per","per "," of","of "," your","your "," power","  "," attack damage"]
pattern = re.compile('[a-zA-Z]')
misc_duration_or_other = ["for","over","+","every", "per second"]
pattern_brac = re.compile(r'(\d+)(\(\+)')
range_radius = [",","-"]
api_errors = {
    r'(isrank\d\/)(\d/)*':"",
    r'(\d|x)(\/ )(\d)':r'\g<1>/\g<3>',
    r'(\()(\d+)':r'\g<1>+\g<2>',
    r"(\d+(\.\d+)?)([x]([a-zA-Z]+))":r"\g<1> \g<4>",
    r"(\d+|\d+\.\d+)(x)":r"\g<1>"
}
max_stax = ["stack","stacking"]
max_hp = ["health","max hp"]
dmg_types = ["physical","magical","level","lvl","health","hp"]
xhp_tokens = ["missing","taken","dealt"]
range_inds = [",","-"]
punctuation= r"""!"#$&'()*+,-/:;<=>?@[\]^_`{|}~"""
#Smite API unrelated columns,DF API unrelated columns
metadata = [
    'AbilityId1', 'AbilityId2', 'AbilityId3', 'AbilityId4', 'AbilityId5',
    'Ability_1', 'Ability_2', 'Ability_3', 'Ability_4', 'Ability_5',
    'AutoBanned', 'Cons','Lore',
    'OnFreeRotation', 'Pros', 'Title', #'basicAttack',
    'godAbility1_URL', 'godAbility2_URL', 'godAbility3_URL',
    'godAbility4_URL', 'godAbility5_URL', 'godCard_URL', 'godIcon_URL',
    'latestGod', 'ret_msg']
number_dict = {
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10
}

#uncomment if using
#df_api_trim = df_api.drop(columns=metadata)

def is_per_hit(num_val):
    return len(re.findall(r"(\d|\d%|\ds)\sper\s(?!level|stack|tick|rank|sec|charge|kill|(\b(\w+)('s)*?\s+level)|\d)",num_val))>0
#supporting functions
#count digits
def count_digits(abl_string):
    return len(re.findall(r'(\d+\.\d+)|(\d+)',abl_string))

#count "/" ranks of any ability
def count_ranks(abl_string):
    return abl_string.count("/")

#convert single str, durations, and % to float
def str_to_num_only(string,percent=None):
    substring = re.sub(r"\D(?!\d)", "", string)
    if percent or "%" in string:
        try:
            return float(substring)/100
        except:
            warnings.warn(f"{getframeinfo(currentframe()).lineno} {string} or {substring} is not a float.")
            return {getframeinfo(currentframe()).lineno :
                (f"{string} or {substring} is not a float.")}
    else:
        try:
            return float(substring)
        
        except:
            warnings.warn(f"{getframeinfo(currentframe()).lineno} {string} or {substring} is not a float.")
            return {getframeinfo(currentframe()).lineno : 
                (f"{string} or {substring} is not a float.")}
 

#convert scaling ability text to tag
def get_dmg_type(abl_val):
    dmg_type = ""
    #tokenize
    if not isinstance(abl_val, list):
        split_tokens = abl_val.lower().split()
    else: 
        split_tokens = abl_val
    for token in split_tokens:
        #if physical
        if  "physical" in token:
            return "physical"
        #if basic
        elif "basic" in token:
            return "basic"
        #if Magical
        elif "magical" in token:
            return "magical"
        #if per level
        elif "level" in token or "lvl" in token:
            return "lvl"
        else:
            pass
    #if HP based
        if "missing" in token or "taken" in token:
            dmg_type += "x"
        if "target" in token:
            dmg_type += "t"
        if "hp" in token or "health" in token:
            if "t" not in dmg_type:
                dmg_type += "m"
            return dmg_type+"hp"
    #if it didn't reach the end with a dmg type > error
    return {getframeinfo(currentframe()).lineno : 
     (f"scaler/dmg_type detection error: {abl_val}")}
        
#older converter used for abilities / if "/" or single & if "%"" or not
def str_to_val_or_percent(abl_str,percent=None):
    #validate input
    if count_digits(abl_str)<1:
        return {getframeinfo(currentframe()).lineno : 
         (f"{abl_str} contains no numbers")}
    else:
        pass
    #add percent flag
    if "%" in abl_str:
        percent=True
    #if a per\lvl abl
    if count_ranks(abl_str)>=1:
        abl_substr = abl_str.split("/")
        return list(map(lambda x: str_to_num_only(x,percent),abl_substr))        
    else:
        abl_substr = abl_str
        return str_to_num_only(abl_substr,percent)
#takes a num_val of abl and amplifies it by a coefficient
def amplify_per_tick(abl_val,coef):
    #validate
    #  if abl is just string
    if isinstance(abl_val,str):
        return {getframeinfo(currentframe()).lineno : 
                            (f"amp validation error, invalid input:\
                            {abl_val,coef}")}
    elif isinstance(abl_val,dict):
        return {getframeinfo(currentframe()).lineno : 
                            (f"amp validation error, input contains errors:\
                            {abl_val,coef}")}
    elif isinstance(coef,str):
        try:
            coef = float(coef)
        except:
            return {getframeinfo(currentframe()).lineno : 
                            (f"amp validation error, coef not number:\
                            {abl_val,coef}")}
    else:
        pass
    #if abl is a list
    if isinstance(abl_val,list):
        amped = []    
        for sublist in abl_val:
            if isinstance(sublist,list):
                amped.append([num * coef if isinstance(num,(float,int)) else num for num in sublist])
            elif isinstance(sublist,dict):
                print("amp:",sublist, abl_val)
            else:
                
                try:
                    amped.append(sublist*coef)
                except:
                    #warnings.warn(f"{getframeinfo(currentframe()).lineno} amp list error, can't multiply: {abl_val,sublist,coef}")
                    return {getframeinfo(currentframe()).lineno : 
                            (f"amp list error, can't multiply:\
                            {abl_val,sublist,coef}")}
        return amped
    #if abl_Val just int/float
    else:
        try:
            return (abl_val*coef)
        except:
            return {getframeinfo(currentframe()).lineno : 
                    (f"amp single error, can't multiply:\
                    {abl_val,coef}")}

#turns a num_val into a [ base , [scaling %, scaler]]
def abl_processor_basic(num_val,key_val=None):
    num_digits=count_digits(num_val)
    #validate input, needs at least one number
    if num_digits==0:
        if key_val:
            return {key_val:num_val}
        else:
            return num_val
    #check non-numerical start
    elif not (num_val[0].isdigit() or num_val[0]=="."):
        for ind,substring in enumerate(num_val):
            if substring.isdigit():
                raw_abl_val = num_val[ind:].strip()
                break
    else:
        raw_abl_val = num_val.strip()
    
    #assume scaling or feature
    if " " in raw_abl_val:
        #format [base_Val ,scaler_val]
        #validate / remove text before /ie. Kaldr gains a dash attack dealing 70/85/100/115/130
        
        base_val, scaler_vals = raw_abl_val.split(" ",1)
        
        #base value of abl
        abl_val = str_to_val_or_percent(base_val)
        #need conditional to spot multiple scalers
        scale_digit_count = count_digits(scaler_vals)
        
        #if more than one number, must be multiple scalers / ie "39 + 2/Lvl (+100% of Physical Power)"
        #TODO Serquet bugged / Value_error: could not convert string to float: "70%    ) +5%  '     ."
        if scale_digit_count>1:
            scale_list =[]
            #for standard scalers only
            if any(ind in scaler_vals for ind in ["(","of"]):
                for val in scaler_vals.split("("):
                    abl_scaling = str_to_num_only(val)
                    abl_scaler = get_dmg_type(val)
                    scale_list.append([abl_scaling,abl_scaler])
            #multiple buffs
            elif "and" in scaler_vals or "&" in scaler_vals:
                scaler_vals = scaler_vals.replace("&","and")
                #validate key
                if not key_val:
                    return {getframeinfo(currentframe()).lineno : 
                            (f"bsc_abl 'and' error, no key_val provided:\
                            {key_val, raw_abl_val}")}
                else:
                    buff_list= raw_abl_val.split("and")
                    buff_dict={}
                    for buff in buff_list:
                        try:
                            new_key=key_val+" "+buff.split(" ")[1]
                            buff_dict[new_key] = str_to_num_only(buff)
                        except:
                            return {getframeinfo(currentframe()).lineno : 
                            (f"bsc_abl 1num+'and' error, extract failed:\
                            {key_val, raw_abl_val}")}
                    return buff_dict
            #unexpected text after numbers
            #not standard scaling
            else: 
                try:
                    #[bsc_abl error, non-stndard scalar:('cost', '10 + 40/50/60/70/80 per second')]
                    
                    abl_val = str_to_num_only(raw_abl_val)
                    if key_val:
                        return {key_val:abl_val}
                    else:
                        return abl_val
                except:
                    return {getframeinfo(currentframe()).lineno : (f"bsc_abl error, non-stndard scalar:{key_val, raw_abl_val}")}
    
            #return section
            if key_val:
                return {key_val:[abl_val,scale_list]}
            else:
                return [abl_val,scale_list]

        #if no numbers get scaler /ie "80/85/90/95/100% scaling" or "15/20/25/30/35 protections"
        elif scale_digit_count==0:

            
            #validate input / must have DMG flag
            if any(flag in raw_abl_val for flag in dmg_types):
                abl_scaling = abl_val
                abl_val = 0
                abl_scaler = get_dmg_type(scaler_vals)
                if key_val:
                    return {key_val:[abl_val,[abl_scaling,abl_scaler]]}
                else:
                    return [abl_val,[abl_scaling,abl_scaler]]
            #per_hit scaling /ie. 5/7/9/11/13 per hit
            elif "per" in scaler_vals:
                if key_val and "cost" in key_val:
                    return {key_val:str_to_val_or_percent(num_val)}
                else:
                #TODO make per hit work
                    return {getframeinfo(currentframe()).lineno : \
                                (f"bsc_abl 'per_hit' error, no solution yet:\
                                {key_val, raw_abl_val}")}
            #buffs and  keys conditionals / ie. 10% physical lifesteal
            #must twp buffs two keys / ie. 2% physical lifesteal and increased healing
            elif "and" in scaler_vals or "&" in scaler_vals:
                scaler_vals = scaler_vals.replace("&","and")
                #validate key
                if not key_val:
                    return {getframeinfo(currentframe()).lineno : 
                            (f"bsc_abl 'and' error, no key_val provided:\
                            {key_val, raw_abl_val}")}
                else:
                    scale_list= scaler_vals.split("and")
                    scale_dict={}
                    for scaler in scale_list:
                        new_key=key_val+" "+scaler
                        scale_dict[new_key] = abl_val
                    return scale_dict
            #if some modified duration, discard /ie "3s when fully deployed"
            elif base_val[-1]=="s":
                if key_val:
                    return {key_val:abl_val}
                else:
                    return abl_val
            #value with descriptor/ ie 9/10.5/12/13.5/15% slow
            else:
                #validated
                if not key_val:
                    return {getframeinfo(currentframe()).lineno : 
                            (f"bsc_abl 0num else error, no key_val provided:\
                            {key_val, num_val}")}
                else:
                    new_key=(key_val+" "+scaler_vals) if len(scaler_vals)>2 else key_val
                    return {new_key:abl_val}
                
        #else / ie  "15/25/35/45/55 (+15% of your Magical Power)"
        else:  
            abl_scaling = str_to_num_only(scaler_vals)
            abl_scaler = get_dmg_type(scaler_vals)
            if key_val:
                return {key_val:[abl_val,[abl_scaling,abl_scaler]]}
            else:
                return [abl_val,[abl_scaling,abl_scaler]]
    #just a number
    else:
        if key_val:
            return {key_val:str_to_val_or_percent(num_val)}
        else:
            return str_to_val_or_percent(num_val)

#get maximum stack values
def extract_max(split_val,per_stack_bonus,base_bonus):

    if isinstance(split_val,list):
        if len(split_val)<=2:
            super_string = split_val[-1].split(" ")
        else:
            super_string = split_val
        for substring in super_string[::-1]:
            #strip punct and return first number
            no_punc_sub = substring.strip("\(\)+")
            #if it was only punctuation
            if not no_punc_sub:
                continue
            if count_digits(no_punc_sub)>=1 and not no_punc_sub[0].isalpha():
                if "%" in no_punc_sub:
                    try:
                        return round((float(re.sub(r'(\d+(\.\d+)?)%',lambda match: str(float(match.group(1)) / 100),no_punc_sub))-base_bonus)/per_stack_bonus)
                    except:
                       return {getframeinfo(currentframe()).lineno : 
                            (f"Operand error: {type(no_punc_sub)} and {type(base_bonus)}: {no_punc_sub} {base_bonus}")}
                elif float(no_punc_sub)<1:
                    pass
                else:
                    return float(no_punc_sub)
            else:
                pass
    elif count_digits(split_val[0])>=1:

        no_punc_sub = split_val.strip("\(\)+")
        if count_digits(no_punc_sub)>=2:
            for substring in no_punc_sub.split()[::-1]:
                if substring.isdigit():
                    return float(substring)
                else:
                    pass
        elif "%"in no_punc_sub:
            return round((float(re.sub(r'(\d+(\.\d+)?)%',lambda match: str(float(match.group(1)) / 100),no_punc_sub))-base_bonus)/per_stack_bonus)
        else:
            return float(no_punc_sub)
    else:
        return {getframeinfo(currentframe()).lineno : 
                            f"{split_val} does not contain/start with a number"}

#main functions
#abl value converters

#per_tick to output
def per_tick_cleaner(str_val,key_val,num_val,desc_tok):
    #chang'e tick uncountable / process as stack
    if "avoided" in num_val:
        tick_as_stack = num_val.replace("per tick avoided","per stack max 5 stacks")
        return stack_converter(str_val,key_val,tick_as_stack,desc_tok)
    else:
        #you are not Chang'e
        pass
    dur_val = 0
    tick_val = 0
    #check the abl_val/num_val for tick and dur /ie  10/14/18/22/26 every 1s for 5s
    abl_split = num_val.split(" ")
    for ind, word in enumerate(abl_split):
        #detect ticks with "every" +"second" 
        if word == "every":
            for next_word in abl_split[ind:ind+5]:
                if "second" in next_word:
                    tick_val = 1
                    break
                elif count_digits(next_word)>=1 and not next_word[0].isalpha():
                    tick_val = str_to_num_only(next_word)
                    break
                else:
                    pass
        #detect durations with "for" , "over"
        elif (word == "for" or word == "over") and count_digits(abl_split[ind+1])>=1:
            dur_val = str_to_num_only(abl_split[ind+1])
        else:
            pass
    #check key for the duration
    if dur_val==0:
        
        for key in str_val:
            #search in abl features for duration / pass if value not highest > avoid CC durs
            if dur_val==0 and ("duration" in list(key.values())[0][:-1].lower() or "lifetime" in list(key.values())[0][:-1].lower()):
                temp_dur = str_to_num_only(list(key.values())[1])
                if temp_dur > dur_val:
                    dur_val = temp_dur
    else:
        pass
    #search the description for tick and dur 
    #iter through description
    if tick_val== 0 or dur_val == 0:
        for ind, word in enumerate(desc_tok):
            #detect "every" +"second" ticks
            if tick_val == 0:
                if word == "every":
                    for next_word in desc_tok[ind:ind+5]:
                        if "second" in next_word:
                            tick_val = 1
                            break
                        elif count_digits(next_word)>=1:
                            tick_val = str_to_num_only(next_word)
                            break
                        elif next_word in list(number_dict.keys()): 
                            tick_val = number_dict[next_word]
                            break
                        else:
                            pass
                elif word == "times" and desc_tok[ind+1]=="over" and (count_digits(desc_tok[ind+2])>=1 or desc_tok[ind+2] in list(number_dict.keys())):
                    try:
                        temp_tick=number_dict[desc_tok[ind-1]]
                    except KeyError:
                        temp_tick=float(desc_tok[ind-1])
                    except:
                        return {getframeinfo(currentframe()).lineno : 
                                ("Tick Detect Token error:",desc_tok[ind-1:ind+3])}
                    try:
                        dur_val=number_dict[desc_tok[ind+2]]
                    except KeyError:
                        dur_val=str_to_num_only(desc_tok[ind+2])
                    except:
                        return {getframeinfo(currentframe()).lineno : 
                                ("Duration Detect Token error:",desc_tok[ind-1:ind+3])}
                    tick_val = temp_tick/dur_val
            else:
                pass
            
            #detect durations with "for" , "over"
            if dur_val==0 and (word == "for" or word == "over"):
                if count_digits(desc_tok[ind+1])>=1:
                    dur_val = str_to_num_only(desc_tok[ind+1])

                elif desc_tok[ind+1] in list(number_dict.keys()):
                    dur_val = number_dict[desc_tok[ind+1]]
                
            else:
                pass
    #there must be these values to process the dmg numbers
    if dur_val==0:
        return {getframeinfo(currentframe()).lineno : 
                            ("Missing Tick/Dur:",
                            tick_val,dur_val,"abl_vals:",key_val, num_val, str_val)}
    elif tick_val == 0 and dur_val!=0:
        tick_val = 1
        #warnings.warn(f"Per tick subbed : {dur_val} to {key_val}, {num_val}, {str_val}")       
    else:
        pass
    #make per_tick duration key
    dur_dict = {key_val+" duration":dur_val}
    # amplify num_val and return
    tick_coefficient = dur_val/tick_val
    #get base_vals
    if "every" in num_val:
        raw_abl_val = abl_processor_basic(num_val.split("every",1)[0])
    else:
        raw_abl_val = abl_processor_basic(num_val)
    #amplify to make a max/min
    max_abl_val = amplify_per_tick(raw_abl_val,tick_coefficient)
    if isinstance(max_abl_val, dict):
            return max_abl_val
    #return
    abl_dict = {key_val+" total":max_abl_val}
    abl_min_dict = {key_val+" min":raw_abl_val}
    return dict(abl_dict,**abl_min_dict,**dur_dict)

#max health based abilities
#convert abl text into hp scale type
#deal with max hp and hp related
def hp_converter(key_val,num_val):
    reqs=["health","hp"]
    #negation conditional / ie 1 hp lost per 5 hits for minions
    if "lost" in num_val:
        return {key_val:num_val}
    else:
        pass
    #bug: serqet poison, erlang
    #(pexistspprop1007/0.70/+#/+70% of your Physical Power) +5% of target's maximum Health as Physical Damage."
    # should be (+70% of your Physical Power) +5% of target's maximum Health as Physical Damage.
    #"value":"(pexistsppropppower/0.075/+#/+5% of your Basic Attack Power)"}]}}
    #(2% of the target's max. health. +5% of your Basic Attack Power)
   #MOVED TO CLEANER if num_val[0:2]=="(p":
    #    if "(pexistspprop1007" in num_val:
    #        num_val = re.sub(r'\(pexistspprop1007\/\d.\d+\/\+#/',"0 ",num_val)
    #    elif "(pexistsppropppower" in num_val:
    #        num_val = re.sub(r'\(pexistsppropppower\/\d.\d+\/\+#/',"0 + 2% of target's maximum health",num_val)
    num_val=num_val.strip()

    #entry conditional / ie 1% max health, 15% of target's max hp
    if any(flag in num_val for flag in reqs) and count_digits(num_val)>=1:
        base_val = 0
        split_val = num_val.split(" ",1)
        scale_count = split_val[-1].count("+")
        #if base+ratio
        if scale_count==1:
            #if scale_val+ratio / ie  '25/30/35/40/45 (+20% of your maximum health)',
            base_val = str_to_val_or_percent(split_val[0])
            abl_ratio = str_to_num_only(split_val[-1])
            dmg_type = get_dmg_type(split_val)
            return {key_val:[base_val,[abl_ratio,dmg_type]]}
        #if more than one scaling
        #TODO multi scalers /ie Serquet
        elif scale_count>1:
            base_val = str_to_val_or_percent(split_val[0])
            ratio_split =split_val[-1].split("+")[1:]
            abl_ratio=list(map(lambda x: str_to_val_or_percent(x),ratio_split))
            dmg_type= list(map(lambda y: get_dmg_type(y),ratio_split))
            return {key_val:[base_val,[[abl_ratio[0],dmg_type[0]],[abl_ratio[1],dmg_type[1]]]]}
        #if ratio only ie. '10% of max hp'
        else:   
            abl_ratio = str_to_val_or_percent(split_val[0])
            return {key_val:[base_val,[abl_ratio,get_dmg_type(split_val)]]}
    #bug report
    else:
        return {getframeinfo(currentframe()).lineno : (f"No health flag or no number detected in:{num_val}")}

#TODO: PER HIT ABLs
def per_hit_abl(str_val,key_val,num_val,desc_tok):
    #set max hits to 0
    per_max = 0
    #get length of desc for iteration calcs
    len_desc = len(desc_tok)
    #make key_list for debugging
    key_list=[]
    #get per_WHAT as token(s)
    per_item = num_val.split("per")[1].strip()
    #if more than one token after split
    if " " in per_item:
        per_item = list(map(lambda x: x.strip(),per_item.split(" ")))
    else:
        per_item = [per_item]
    #expand per_item tokens
    for token in key_val.split(" "):
        if token and ("damage" not in token):
            per_item.append(token)
    #unmentioned flags 
    per_item.append("bounce")

    #search desc for token
    for ind,token in enumerate(desc_tok):
        #stop if a match with per_item token
        if any(item in token for item in per_item):
            min_index = max(ind-5,0)
            max_index = min(ind+5,len_desc)
            #search around the match for any number
            for subtoken in desc_tok[min_index:max_index]:
                if subtoken.isdigit():
                    per_max = float(subtoken)
                    break
                elif subtoken in list(number_dict.keys()):
                    per_max = number_dict[subtoken]
                    break
    #search key vals for token
    if not per_max:
        for key in str_val:
            key_name = list(key.values())[0].lower()
            key_list.append(key_name)
            #search in keys / stop on first 
            if any(item in key_name for item in per_item) and (key_name not in key_val) and count_digits(list(key.values())[1].lower())>0:
                per_max = str_to_val_or_percent(list(key.values())[1].lower())
                break
    #exit validator
    if not per_max:
        return {getframeinfo(currentframe()).lineno : 
                (f"PER_HIT err: no max for {key_val}:{num_val} in {key_list}")} 
    #amplifier
    else:
        #get base_vals
        min_abl_val = str_to_val_or_percent(num_val)
        #amplify to make a max/min
        max_abl_val = amplify_per_tick(min_abl_val,per_max)
        if isinstance(max_abl_val, dict):
            return max_abl_val
        #return
        abl_max_dict = {key_val+" max":max_abl_val}
        abl_min_dict = {key_val+" min":min_abl_val}
        return dict(abl_max_dict,**abl_min_dict)
        
               

#convert stacks into tags and etc
# chcker needed? if "stack" in num_val
def stack_converter(str_val,key_val,num_val,desc_tok): 
    # example outputs
    # [0,[0.04,"stax"], 3  / {"description":"Shadow Slow:","value":"4% Stacking 3 times"}
    #not used for max entries
    if "max" in key_val:
        return {key_val:num_val}
    elif num_val[0]=="-":
        return {key_val:num_val}
    digit_count = count_digits(num_val)
    #check for at least one number
    if digit_count>=1: # any(flag in split_val[-1] for flag in max_indicators):# and :
        
        #cleaning zeroes, adding space after "+" and digit
        num_val = re.sub(r'\+(\d)',r'+ \1',num_val)#.replace("0.",".")
        #create split_val ,as needed
        if " " in num_val:
            split_val=num_val.split(" ",1)
        else:
            split_val=num_val
        base_bonus = 0
        max_val=0
        per_stack_bonus = 0
        dur_dict={}
       
        #formatting: remove if key has "per stack"
        if not "per stack" in key_val:
            stack_key = key_val+" per stack"
            max_key = key_val+" max stacks"
        else:
            stack_key = key_val
            max_key = key_val.replace(" per stack"," max stacks").strip()
        
        #if scaling stacker / ie '2/3/4/5/6 max 5 stacks'
        if count_ranks(split_val[0])>1:
            per_stack_bonus = list(map(lambda x: float(x), split_val[0].split("/")))
            max_val = extract_max(split_val,per_stack_bonus,base_bonus)
            stack_dict = {stack_key:[base_bonus,[per_stack_bonus,"stax"]]}
            if max_val:
                max_dict = {max_key:max_val}
                return dict(stack_dict, **max_dict)
        #if non-scaling stack value / ie. '4% per stack/ max 8 stacks'
        else:
            #tokenize for efficiency
            temp_split = num_val.split(" ")
            #if [0] is not a number, re-declare the  split_val
            if temp_split[0][0].isdigit():
                per_stack_bonus = str_to_num_only(temp_split[0])
                token_split = temp_split[1:]
            else:
                for ix, i in enumerate(temp_split):
                    if count_digits(i)>=1:
                        #format first number as a float
                        per_stack_bonus = str_to_num_only(i)
                        token_split=temp_split[ix+1:]                    
                        break

            #if stacker + max + other / ie '10% + 5% per enemy hit (max. 3 stacks)'
            if digit_count>=2 and not "per stack" in split_val[-1]:
                #if there's a base value plus a scaling value / 10% + 5% per enemy hit (max. 3 stacks)
                if "+" in token_split[0] and count_digits(token_split[1])>=1:
            
                    if any("level" in token for token in token_split[::-1]):
                        #calc per level bonus
                        
                        per_stack_lvl = float(re.sub(r'(\d+(\.\d+)?)%',lambda match: str(float(match.group(1)) / 100),token_split[1]))
                        max_val = extract_max(token_split,per_stack_bonus,base_bonus)
                        stack_dict = {stack_key:[base_bonus,[[per_stack_lvl,"lvl"],[per_stack_bonus,"stax"]]]}
                        if max_val:
                            max_dict = {max_key:max_val}
                            return dict(stack_dict, **max_dict)
                    else:
                        base_bonus = per_stack_bonus
                        per_stack_bonus = float(re.sub(r'(\d+(\.\d+)?)%',lambda match: str(float(match.group(1)) / 100),token_split[1]))
                        max_val = extract_max(token_split,per_stack_bonus,base_bonus)
                        stack_dict = {stack_key:[base_bonus,[per_stack_bonus,"stax"]]}
                        if max_val:
                            max_dict = {max_key:max_val}
                            return dict(stack_dict, **max_dict)
                #if duration? / ie '10% for 1.5s (+3 stacks max.)'
                elif "for" in token_split:
                    #find the duration
                    for tok in token_split:
                        if tok[-1]=="s":
                            dur_val = float(tok[:-1])
                            break
                    #bug catcher, in duration loop but no dur detected
                    if not dur_val:
                        return {getframeinfo(currentframe()).lineno : (f"No duration detectedin {token_split}")}
                    
                    max_val = extract_max(split_val,per_stack_bonus,base_bonus)
                    dur_dict={stack_key+" duration": dur_val}
                    stack_dict = {stack_key:[base_bonus,[per_stack_bonus,"stax"]]}
                    if max_val:
                        max_dict = {max_key:max_val}
                        return dict(stack_dict, **max_dict, **dur_dict)
                #if max_val and stacks / ie. 50% total at max 50 stacks or 15 at 5 stacks
                elif "at" in token_split or "stacking" in token_split:
                    max_val = extract_max(token_split,per_stack_bonus,base_bonus)
                    stack_dict = {stack_key:[base_bonus,[(per_stack_bonus/max_val),"stax"]]}
                    if max_val:
                        max_dict = {max_key:max_val}
                        return dict(stack_dict, **max_dict)            
                #bug catcher
                else:
                    return {getframeinfo(currentframe()).lineno : 
                            (f"No plus or duration detected in {str_val}:{token_split} or {split_val}")}
            #if stack total or per_stack only / ie ."0.2% per stack"
            else:
                
                max_val = extract_max(split_val,per_stack_bonus,base_bonus)
                max_dict = {max_key:max_val}
                stack_dict = {stack_key:[base_bonus,[per_stack_bonus,"stax"]]}
            #if detection fails
            if  base_bonus == 0 and per_stack_bonus == 0:
                return {getframeinfo(currentframe()).lineno : 
                            (f"last resort error: no digit detected: {key_val},{num_val},{split_val} ")}
        #if max not detected in num_val
        if max_val == 0 or max_val == None:
            #search description for max counter
            for ind, word in enumerate(desc_tok):
                
                # check for "stacks" and grab the number before
                if ("stacks" in word or "essence" in word):
                    if desc_tok[ind-1].isdigit():
                        max_val = float(desc_tok[ind-1])
                        max_dict = {max_key:max_val}
                        break
                    elif desc_tok[ind-1] in list(number_dict.keys()):
                    
                        max_val = number_dict[desc_tok[ind-1]]
                        max_dict = {max_key:max_val}
                        break
                    else:    
                        pass
                elif "max" in word:
                    for substring in desc_tok[ind:ind+5]:
                        if substring.isdigit():
                            try:
                                max_val = float(substring)
                                max_dict = {max_key:max_val}      
                                return dict(stack_dict, **max_dict)  
                            except:
                                return {getframeinfo(currentframe()).lineno : 
                                    (f"max error: no max digit detected: {key_val},{num_val},{desc_tok} ")}
                        elif substring in list(number_dict.keys()):
                            max_val = number_dict[substring]
                            max_dict = {max_key:max_val}
                            return dict(stack_dict, **max_dict)
                            

                else:
                    pass
            for key in str_val:
                #search in abl features for max 
                if "max" in list(key.values())[0].lower():
                    max_val = extract_max(list(key.values())[1],per_stack_bonus,base_bonus)
                    max_dict = {max_key:max_val}
                    if max_val:
                        max_dict = {max_key:max_val}
                        return dict(stack_dict, **max_dict)  
                    break
                else:
                    pass 
        #validate output and send
        if max_val == 0 or per_stack_bonus==0:
            return {getframeinfo(currentframe()).lineno : 
                            (f"per stack bonus not detected: {key_val},{num_val},{split_val};max: {max_val}, per:{per_stack_bonus} or base:{base_bonus} or desc: {desc_tok}")}
        else:
            if dur_dict:
                return dict(stack_dict, **max_dict, **dur_dict)
            else:
                return dict(stack_dict, **max_dict)
    #bug catcher
    else:
        return {getframeinfo(currentframe()).lineno : (f"This is not a stacking ability: {key_val},{num_val},{split_val}")}

#fix API errors
def fix_API_errors(key_val,num_val):
     #fix trailing blanks
        
   
    #fix api key_val errors/inconsistency
    if key_val:
        if "lifetime" in key_val:
            key_val = key_val.replace('lifetime',"duration")
    
    #fix max HP items
    if num_val:
         #fix api num_val errors
        if len(num_val)>8:
            #cycle through error list
            for i in list(api_errors.keys()):       
                temp_val= re.compile(i).sub(api_errors[i],num_val)
                #check if any change happened
                if temp_val != num_val:
                    num_val= temp_val
                    break
        #fix extra spaces
        num_val=num_val.strip()
        #fix Seruqet/Erlang
        if num_val[0:2]=="(p":
            if "(pexistspprop1007" in num_val:
                num_val = re.sub(r'\(pexistspprop1007\/\d.\d+\/\+#/',"0 ",num_val)
            elif "(pexistsppropppower" in num_val:
                num_val = re.sub(r'\(pexistsppropppower\/\d.\d+\/\+#/',"0 + 2% of target's maximum health",num_val)
        #fix / convert "tide" to stacks
        if "tide" in num_val:
            val = num_val.replace("tide level", "tide")
            val = val.replace("max tide", "max 1 stacks")
            val = val.replace("tide","stacks")
            num_val = val.replace("on max","at max")
        #remove extra pluses
        if num_val[0]=="+":
            num_val = num_val[1:]
    
    #bug-fix Yemoja
    if key_val and num_val:
        if "omi" in key_val and "and" in num_val:
                num_val = num_val.replace(" and ", "/") 
    return key_val.lower(),num_val.lower()

# convert _ + _ or _ (_% + phy) 
def scaler_converter(key_val,num_val,desc_val):
## account for format errors: lack of space, remove double-space
    num_val = num_val.replace(" + "," +")

    if count_digits(num_val[(num_val.find("("))-1])>=1:
        spaced_val = re.sub(pattern_brac, r'\1 \2', num_val)
        result = spaced_val.split(" ",1)
    else:
        result = num_val.split(" ",1)
    #check per level and reformat
    if count_ranks(result[0])>1:
        try:
            result[0] = list(map(float,result[0].split("/")))
        except:
            return {getframeinfo(currentframe()).lineno:("vals per level error:",result[0],"whole val:",desc_val,":",getframeinfo(currentframe()).lineno)}
            
    #split bracket scaler and /lvl vals 
    try:
        result[1] = result[1].split(" ",1)
    except:
        return {getframeinfo(currentframe()).lineno:("scaler spliting error:",result,"whole val:",desc_val,":",getframeinfo(currentframe()).lineno)}
        

    #iter through and remove text/punct from scaler as needed

    for xi,i in enumerate(result[1]):
        #remove punct
        result[1][xi]=result[1][xi].translate(str.maketrans("","","\(\)+")).replace("/Lvl"," per level")
        #remove scaler tags
        for s in scalers:
            result[1][xi] = result[1][xi].lower().replace(s,"")
        #TODO " " detection causing problems
        #if two scalers, split into two lists
        if " " in result[1][xi]:
            result[1][xi]=result[1][xi].split(" ",1)
            #convert into floats        
            for xj, j in enumerate(result[1][xi]):
                if "%" in j:
                    try:
                        result[1][xi][xj] = float(result[1][xi][xj].translate(str.maketrans("","","%+/\\")))*.01
                    except:
                        return {getframeinfo(currentframe()).lineno:("percent error:",result[1][xi][xj],";",result,"whole val:",desc_val, getframeinfo(currentframe()).lineno)}
                        
                try:
                    result[1][xi][xj] = float(result[1][xi][xj]) 
                except:
                    pass
        #format percents
        elif "%" in i:
            try:
                result_per = float(result[1][xi].translate(str.maketrans("","","%+/\\")))*.01
                result[1][xi] = result_per
            except:
                return {getframeinfo(currentframe()).lineno:("% convert error:",(result[1][xi][:-1]),";",result,"whole val:",desc_val,getframeinfo(currentframe()).lineno)}
                
        try:
            result[1][xi] = float(result[1][xi]) 
        except:
            pass
        #return
        return {key_val:result}

#convert complex durations
#split eff and duration
def convert_dur_eff(str_val,key_val,num_val,desc_val,desc_tok):
    result_dict={}
    temp_val = list(map(lambda x: x.strip(),num_val.split(" ",1)))
    #get effect
    try:
        eff_val=str_to_val_or_percent(temp_val[0])
        result_dict[key_val] = eff_val
        raw_dur_val=temp_val[1]
        dur_digits = count_digits(raw_dur_val)
    except:
        return {getframeinfo(currentframe()).lineno:("dur effect split error:",key_val,temp_val,";",desc_val,getframeinfo(currentframe()).lineno)}
                  
    #get duration
    if dur_digits==1:
        try: 
            dur_val = str_to_num_only(raw_dur_val)
            result_dict[key_val+" duration"] = dur_val
      
            return result_dict
        except:
            return {getframeinfo(currentframe()).lineno:("dur-effect per-second abl error:",key_val,raw_dur_val,eff_val,";",desc_val,getframeinfo(currentframe()).lineno)}
    #if there is no duration            
    elif dur_digits==0:
        for key in str_val:
            #search in abl features for max 
            if "duration" in list(key.values())[0].lower() or "lifetime" in list(key.values())[0].lower():
                dur_val = str_to_num_only(list(key.values())[1])
                result_dict[key_val+" duration"] = dur_val
                return result_dict
            else:
                pass 
        # check description for "seconds" and grab the number before
        for ind, word in enumerate(desc_tok):
            if "for" in word:
                for substring in desc_tok[ind:ind+5]:
                    if count_digits(substring)>=1:
                        try:
                            dur_val = str_to_num_only(substring)
                            result_dict[key_val+" duration"] = dur_val
                            return result_dict
                        except:
                            return {getframeinfo(currentframe()).lineno : 
                            (f"max error: no max digit detected: {key_val},{num_val},{desc_tok} ")   }
                    elif substring in list(number_dict.keys()):
                        dur_val = number_dict[substring]
                        result_dict[key_val+" duration"] = dur_val
                        return result_dict
            else:
                pass
        return {getframeinfo(currentframe()).lineno:
                ("dur-effect dur_value not detected error:",key_val,raw_dur_val,eff_val,";",desc_val,getframeinfo(currentframe()).lineno)}
    #if theres 2 or more numbers
    elif dur_digits==2:
        return per_tick_cleaner(str_val,key_val,num_val,desc_tok)
    else: 
        return {getframeinfo(currentframe()).lineno:
                ("dur-effect dur_value error:",key_val,raw_dur_val,eff_val,";",desc_val,getframeinfo(currentframe()).lineno)}
                                 
#convert range/radius values
def aoe_to_val(key_val,num_val):
    split_key = key_val.split("/")
    #arbitrary value for globals
    if "global" in num_val:
        num_val=num_val.replace("global","800")
    #if range or radius have variable values
    if len(re.findall(",",num_val))>0:
        new_split = []
        sub_strings = [sub_val.split("/") if "/" in sub_val else sub_val for sub_val in num_val.split(',')]
        
        for sub_string in sub_strings:
            if isinstance(sub_string,list):    
                try:
                    new_split.append(list(map(lambda x: str_to_num_only(x),sub_string)))
                except:
                    return {getframeinfo(currentframe()).lineno:("range/radius scale error:",key_val,sub_string,sub_strings,getframeinfo(currentframe()).lineno)}
                    
            #else dump single val
            else:
                try:
                    new_split.append(str_to_num_only(sub_string))
                except:
                    return {getframeinfo(currentframe()).lineno:("range/radius scale error:",key_val,sub_string,sub_strings,getframeinfo(currentframe()).lineno)}
                    
        split_val = new_split
    #if only range and radius single va;s
    else:
        split_val = list(map(lambda x: str_to_num_only(x),num_val.split("/")))

    try:
        output_dict={}
        for ix,i in enumerate(split_key):
            output_dict[str(split_key[ix])]=split_val[ix]
        return output_dict
            
    except:
        return {getframeinfo(currentframe()).lineno:("range/radius error:",split_key,split_val,getframeinfo(currentframe()).lineno)}
 

def scale_abl_converter(key_val,num_val):
    scale_dict={}
    #if the value is _ to _
    if "to" in num_val:
        split_val = list(map(lambda x: str_to_val_or_percent(x),num_val.split("to")))
        key_min = key_val.replace("scale","minimum")
        key_max = key_val.replace("scale","maximum")
        scale_dict[key_min]=find_minimum(split_val)
        scale_dict[key_max]=find_maximum(split_val)
        return scale_dict
    #if you're Eset
    else:
        return aoe_to_val(key_val,num_val)
    
def find_maximum(input_list):
    max_value = float('-inf')  # Set initial max_value to negative infinity

    for item in input_list:
        if isinstance(item, list):  # If item is a sublist, recursively call the function
            sublist_max = find_maximum(item)
            max_value = max(max_value, sublist_max)
        else:
            try:
                max_value = max(max_value, item)  # Update max_value if item is greater
            except:
                return {getframeinfo(currentframe()).lineno : 
                            (f"minimum val error; {input_list} or {item} vs {max_value} does not compare.")}
    return max_value

def find_minimum(input_list):
    min_value = float('+inf')  # Set initial min_value to negative infinity

    for item in input_list:
        if isinstance(item, list):  # If item is a sublist, recursively call the function
            sublist_min = find_minimum(item)
            min_value = min(min_value, sublist_min)
        else:
            try:
                min_value = min(min_value, item)  # Update min_value if item is greater
            except:
                return {getframeinfo(currentframe()).lineno : 
                            (f"minimum val error; {input_list} or {item} vs {min_value} does not compare.")}
    return min_value