def round(precision):.*pow(10;precision)|round/pow(10;precision);

def e2t(epoch): (epoch | tostring | .[:10] | strptime("%s") | strftime("%Y-%m-%d %H:%M:%S")) ;
