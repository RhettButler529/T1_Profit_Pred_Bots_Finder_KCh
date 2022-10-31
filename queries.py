
def fetch_addresses_query(date, to_addr, offset):
    
    query = """{
            ethereum(network: bsc) {
                    transactions(
                    time: {after: "%s"}
                    txTo:{is:"%s"}
                    options:{desc:"count", limit:25000, offset:%s}
                    success:true

                    ) {
                    count

                    sender{
                        address
                    }      
                    maximum(of: time)

                    }
                }
            }"""
            
    return query % (date, to_addr, offset)


def fetch_tx_query(date, addr, offset, sender=False):
    
    query = """{
            ethereum(network: bsc) {
                    transactions(
                    time: {after: "%s"}
                    %s:{is:"%s"}
                    options:{limit:25000, offset:%s}
                    success:true
                    ) {
                        hash
                    }
                }
            }"""
            
    return query % (date, "txSender" if sender else "txTo", addr, offset)


def get_txs(date, contract_addr, sender_addr, methods:list, offset):
    
    query = """    
            query MyQuery {
                ethereum(network: bsc) {
                    smartContractCalls(
                        txFrom: {is: "%s"}
                        time: {after: "%s"}
                        any: {smartContractAddress: {is: "%s"}, smartContractMethod: {in: %s}}
                        options: {limit:1000, offset:%s}
                    ) {
                        transaction {
                        hash
                        }
                    }
                }
            }"""
    
    query = query % (sender_addr, date, contract_addr, methods.__str__(), offset)
     
    return query.replace("'", '"') 


def get_balance_query(addr, date=None):
    
    query = """{
            ethereum(network: bsc) {
                    address(address: {is: "%s"}){
                    balances(
                    %s
                    currency: {is: "BNB"}
                    ) {
                    value
                    }
                    }
                }
            }"""
            
    return query % (addr, 'time: {till: "%s"},' % date) if date else query % (addr, "")


def get_transfer_query(date, addr, contract_addr, offset, tansfer_in:bool):
    
    if tansfer_in:
        query = """
                query MyQuery {
                    ethereum(network: bsc) {
                            transactions(
                            amount: {gt: 0}
                            time: {after: "%s"}
                            txTo: {is: "%s"}
                            success: true
                            options: {limit:1000, offset:%s}
                            ) {
                            any(of: amount)
                            hash
                            sender {
                                smartContract {
                                    contractType
                                }
                            }
                        }
                    }
                }"""
        
        return query % (date, addr, offset)
            
    else:        
        query = """    
                query MyQuery {
                    ethereum(network: bsc) {
                            transactions(
                            success: true
                            amount: {gt: 0}
                            date: {after: "%s"}
                            txSender: {is: "%s"}
                            txTo: {not: "%s"}
                            options: {limit:1000, offset:%s}
                            ) {
                            any(of: amount)
                            hash
                            to {
                                smartContract {
                                    contractType
                                }
                            }
                        }
                    }
                }"""
            
        return query % (date, addr, contract_addr, offset)

