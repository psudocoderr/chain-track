// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SupplyChain
 * @dev Tracks product lifecycle from Manufacturer → Distributor → Retailer → Customer
 */
contract SupplyChain {

    // ─── Enums ────────────────────────────────────────────────────────────────
    enum Role        { Manufacturer, Distributor, Retailer, Customer }
    enum ProductStatus { Created, InTransit, Delivered, Sold }

    // ─── Structs ──────────────────────────────────────────────────────────────
    struct Participant {
        address addr;
        string  name;
        Role    role;
        bool    isRegistered;
    }

    struct TrackingEvent {
        address actor;
        string  actorName;
        Role    actorRole;
        ProductStatus status;
        string  location;
        uint256 timestamp;
        string  notes;
    }

    struct Product {
        uint256       id;
        string        name;
        string        description;
        address       manufacturer;
        address       currentOwner;
        ProductStatus status;
        uint256       createdAt;
        uint256       price;          // in wei
        bool          exists;
    }

    // ─── State variables ──────────────────────────────────────────────────────
    address public admin;
    uint256 private nextProductId = 1;

    mapping(uint256 => Product)          public  products;
    mapping(uint256 => TrackingEvent[])  private productHistory;
    mapping(address => Participant)      public  participants;

    uint256[] public allProductIds;

    // ─── Events ───────────────────────────────────────────────────────────────
    event ParticipantRegistered(address indexed addr, string name, Role role);
    event ProductCreated(uint256 indexed productId, string name, address indexed manufacturer);
    event OwnershipTransferred(uint256 indexed productId, address indexed from, address indexed to, ProductStatus newStatus);
    event ProductSold(uint256 indexed productId, address indexed retailer, address indexed customer);

    // ─── Modifiers ────────────────────────────────────────────────────────────
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier onlyRegistered() {
        require(participants[msg.sender].isRegistered, "Participant not registered");
        _;
    }

    modifier productExists(uint256 _productId) {
        require(products[_productId].exists, "Product does not exist");
        _;
    }

    modifier onlyCurrentOwner(uint256 _productId) {
        require(products[_productId].currentOwner == msg.sender, "You are not the current owner");
        _;
    }

    // ─── Constructor ──────────────────────────────────────────────────────────
    constructor() {
        admin = msg.sender;
        // Register admin as a participant too
        participants[msg.sender] = Participant({
            addr: msg.sender,
            name: "Admin",
            role: Role.Manufacturer,
            isRegistered: true
        });
    }

    // ─── Participant Management ───────────────────────────────────────────────

    /**
     * @dev Register a participant with a role
     */
    function registerParticipant(
        address _addr,
        string memory _name,
        Role _role
    ) external onlyAdmin {
        require(!participants[_addr].isRegistered, "Already registered");
        participants[_addr] = Participant({
            addr: _addr,
            name: _name,
            role: _role,
            isRegistered: true
        });
        emit ParticipantRegistered(_addr, _name, _role);
    }

    // ─── Product Lifecycle ────────────────────────────────────────────────────

    /**
     * @dev Create a new product (only Manufacturers)
     */
    function createProduct(
        string memory _name,
        string memory _description,
        uint256 _price,
        string memory _location,
        string memory _notes
    ) external onlyRegistered returns (uint256) {
        require(
            participants[msg.sender].role == Role.Manufacturer,
            "Only manufacturers can create products"
        );

        uint256 productId = nextProductId++;

        products[productId] = Product({
            id:           productId,
            name:         _name,
            description:  _description,
            manufacturer: msg.sender,
            currentOwner: msg.sender,
            status:       ProductStatus.Created,
            createdAt:    block.timestamp,
            price:        _price,
            exists:       true
        });

        allProductIds.push(productId);

        // Log the creation event
        productHistory[productId].push(TrackingEvent({
            actor:     msg.sender,
            actorName: participants[msg.sender].name,
            actorRole: Role.Manufacturer,
            status:    ProductStatus.Created,
            location:  _location,
            timestamp: block.timestamp,
            notes:     _notes
        }));

        emit ProductCreated(productId, _name, msg.sender);
        return productId;
    }

    /**
     * @dev Transfer product ownership to next party in chain
     * Flow: Manufacturer → Distributor → Retailer
     */
    function transferOwnership(
        uint256 _productId,
        address _to,
        string memory _location,
        string memory _notes
    )
        external
        onlyRegistered
        productExists(_productId)
        onlyCurrentOwner(_productId)
    {
        require(participants[_to].isRegistered, "Recipient is not registered");

        Role fromRole = participants[msg.sender].role;
        Role toRole   = participants[_to].role;

        // Enforce valid transfer chain
        require(
            (fromRole == Role.Manufacturer && toRole == Role.Distributor) ||
            (fromRole == Role.Distributor  && toRole == Role.Retailer),
            "Invalid transfer: must follow Manufacturer->Distributor->Retailer"
        );

        products[_productId].currentOwner = _to;
        products[_productId].status       = ProductStatus.InTransit;

        productHistory[_productId].push(TrackingEvent({
            actor:     msg.sender,
            actorName: participants[msg.sender].name,
            actorRole: fromRole,
            status:    ProductStatus.InTransit,
            location:  _location,
            timestamp: block.timestamp,
            notes:     _notes
        }));

        emit OwnershipTransferred(_productId, msg.sender, _to, ProductStatus.InTransit);
    }

    /**
     * @dev Retailer confirms receipt / marks as Delivered
     */
    function confirmDelivery(
        uint256 _productId,
        string memory _location,
        string memory _notes
    )
        external
        onlyRegistered
        productExists(_productId)
        onlyCurrentOwner(_productId)
    {
        require(
            participants[msg.sender].role == Role.Retailer ||
            participants[msg.sender].role == Role.Distributor,
            "Only distributors or retailers can confirm delivery"
        );
        require(
            products[_productId].status == ProductStatus.InTransit,
            "Product must be in transit to confirm delivery"
        );

        products[_productId].status = ProductStatus.Delivered;

        productHistory[_productId].push(TrackingEvent({
            actor:     msg.sender,
            actorName: participants[msg.sender].name,
            actorRole: participants[msg.sender].role,
            status:    ProductStatus.Delivered,
            location:  _location,
            timestamp: block.timestamp,
            notes:     _notes
        }));
    }

    /**
     * @dev Mark product as sold to a customer
     */
    function sellToCustomer(
        uint256 _productId,
        address _customer,
        string memory _location,
        string memory _notes
    )
        external
        onlyRegistered
        productExists(_productId)
        onlyCurrentOwner(_productId)
    {
        require(
            participants[msg.sender].role == Role.Retailer,
            "Only retailers can sell to customers"
        );
        require(participants[_customer].isRegistered, "Customer must be registered");
        require(
            participants[_customer].role == Role.Customer,
            "Recipient must have Customer role"
        );

        products[_productId].currentOwner = _customer;
        products[_productId].status       = ProductStatus.Sold;

        productHistory[_productId].push(TrackingEvent({
            actor:     msg.sender,
            actorName: participants[msg.sender].name,
            actorRole: Role.Retailer,
            status:    ProductStatus.Sold,
            location:  _location,
            timestamp: block.timestamp,
            notes:     _notes
        }));

        emit ProductSold(_productId, msg.sender, _customer);
    }

    // ─── View Functions ───────────────────────────────────────────────────────

    function getProduct(uint256 _productId)
        external
        view
        productExists(_productId)
        returns (Product memory)
    {
        return products[_productId];
    }

    function getProductHistory(uint256 _productId)
        external
        view
        productExists(_productId)
        returns (TrackingEvent[] memory)
    {
        return productHistory[_productId];
    }

    function getAllProductIds() external view returns (uint256[] memory) {
        return allProductIds;
    }

    function getParticipant(address _addr) external view returns (Participant memory) {
        return participants[_addr];
    }

    function getTotalProducts() external view returns (uint256) {
        return allProductIds.length;
    }
}
